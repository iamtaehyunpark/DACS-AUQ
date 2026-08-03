#!/usr/bin/env bash
# Run the HotpotQA entangled arms back to back, smallest first, one model on the
# box at a time.
#
# Order is deliberate: phi4mini -> gemma4b -> mistral7b complete BEFORE llama70b
# starts. The smalls need one GPU at a 0.30 reservation and finish quickly, so
# any prompt-format or tokenizer problem surfaces cheaply; Llama-70B needs two
# cards at 0.90 and is the expensive thing to discover a bug on. Putting it last
# also means a full chain that dies at the 70B still leaves three finished arms.
#
# RESUMABLE at two levels. An arm that finished is skipped by its ARM_COMPLETE
# marker without loading weights. An arm that died mid-way resumes at shard
# granularity inside run_hotpot_arm.sh. So re-running this script after any
# failure — broken server, OOM, killed session — costs only the work that had
# not finished, never an arm and never the chain.
#
# A failing arm does NOT stop the chain. It is recorded and the next model runs,
# because one bad model should not block the other five. The exit code is
# non-zero if any arm failed, and the summary names them.
#
# Usage: run_hotpot_chain.sh [N_EPISODES=500] [CONCURRENCY=4] [SHARDS=20]
#   HOTPOT_ARMS="phi4mini gemma4b"  restrict/reorder the chain
#   HOTPOT_JUDGE=1                  run the Azure judge after each arm, in the
#                                   background (no GPU, so it overlaps the next
#                                   model's generation for free)
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
N_EPISODES=${1:-500}
CONC=${2:-4}
SHARDS=${3:-20}

# Smallest first; llama70b last. qwen35b is already done and is not in the chain.
ARMS=${HOTPOT_ARMS:-"phi4mini gemma4b mistral7b llama70b"}

# Distinct port per arm so a leftover server from a killed run cannot be mistaken
# for this one's. 8002 belongs to another user; stay clear of it.
port_for() {
  case "$1" in
    phi4mini) echo 8071 ;; gemma4b) echo 8072 ;; mistral7b) echo 8073 ;;
    llama8b)  echo 8074 ;; llama70b) echo 8075 ;; qwen35b) echo 8076 ;;
    *) echo 8079 ;;
  esac
}

# GPUs 0-2 carry another user's ~16GB; 3 and 4 were the free pair. Pin rather than
# scan, so we never land on a shared card. HOTPOT_GPU_SMALL / HOTPOT_GPU_BIG
# override without editing the script.
GPU_SMALL=${HOTPOT_GPU_SMALL:-4}
GPU_BIG=${HOTPOT_GPU_BIG:-3,4}
gpu_for() { case "$1" in llama70b) echo "$GPU_BIG" ;; *) echo "$GPU_SMALL" ;; esac; }

# Refuse to start a pinned arm if someone else moved onto those cards in the
# meantime — better to skip it than to OOM halfway through and lose the shard.
gpus_free() {
  local want=$1 need=$2 g used total free
  for g in $(echo "$want" | tr ',' ' '); do
    read -r used total < <(nvidia-smi -i "$g" --query-gpu=memory.used,memory.total \
      --format=csv,noheader,nounits 2>/dev/null | tr -d ',')
    [ -n "${used:-}" ] || return 1
    free=$((total - used))
    [ "$free" -ge "$need" ] || { echo "  GPU $g has only ${free}MiB free, need ${need}MiB" >&2; return 1; }
  done
  return 0
}

started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "chain start $started"
echo "arms: $ARMS"
echo "episodes=$N_EPISODES shards=$SHARDS concurrency=$CONC judge=${HOTPOT_JUDGE:-0}"

ok=(); failed=(); skipped=(); judge_pids=()

for KEY in $ARMS; do
  OUT=$RD/result/hotpot_$KEY
  echo
  echo "================ $KEY ================"

  if [ -e "$OUT/ARM_COMPLETE" ]; then
    echo "skip: already complete ($(cat "$OUT/ARM_COMPLETE"))"
    skipped+=("$KEY")
  else
    GPUS=$(gpu_for "$KEY")
    case "$KEY" in llama70b|qwen35b) NEED=78000 ;; *) NEED=28000 ;; esac
    echo "gpus=$GPUS (need ${NEED}MiB each)"
    if ! gpus_free "$GPUS" "$NEED"; then
      echo "$KEY: SKIPPED — pinned GPUs are busy; re-run when they free up" >&2
      failed+=("$KEY(gpu-busy)")
      continue
    fi
    HOTPOT_PORT=$(port_for "$KEY") HOTPOT_GPU=$GPUS \
      bash "$SCRIPT_DIR/run_hotpot_arm.sh" "$KEY" "$N_EPISODES" "$CONC" "$SHARDS"
    rc=$?
    if [ "$rc" -eq 0 ]; then
      echo "$KEY: OK"
      ok+=("$KEY")
    else
      # Deliberately not fatal: the next model still gets its turn, and re-running
      # the chain resumes this arm from its unfinished shards.
      echo "$KEY: FAILED (rc=$rc) — chain continues; re-run to resume this arm" >&2
      failed+=("$KEY")
      continue
    fi
  fi

  # The judge needs no GPU, so it overlaps the next arm's generation. Backgrounded
  # per arm and reaped at the end rather than waited on here.
  if [ "${HOTPOT_JUDGE:-0}" = "1" ]; then
    echo "judge: launching in background for $KEY"
    bash "$SCRIPT_DIR/run_hotpot_judge.sh" "$OUT" > "$OUT/chain_judge.log" 2>&1 &
    judge_pids+=($!)
  fi
done

if [ "${#judge_pids[@]}" -gt 0 ]; then
  echo
  echo "waiting for ${#judge_pids[@]} background judge pass(es)"
  for p in "${judge_pids[@]}"; do wait "$p" || echo "a judge pass failed — see */chain_judge.log" >&2; done
fi

echo
echo "================ summary ================"
echo "start $started  end $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "completed: ${ok[*]:-none}"
echo "skipped (already done): ${skipped[*]:-none}"
echo "failed: ${failed[*]:-none}"
for KEY in $ARMS; do
  OUT=$RD/result/hotpot_$KEY
  u=0; p=0; j=0
  [ -e "$OUT/uq_hotpot_entangled.jsonl" ]     && u=$(wc -l < "$OUT/uq_hotpot_entangled.jsonl")
  [ -e "$OUT/probes_hotpot_entangled.jsonl" ] && p=$(wc -l < "$OUT/probes_hotpot_entangled.jsonl")
  [ -e "$OUT/judge_hotpot_entangled.jsonl" ]  && j=$(wc -l < "$OUT/judge_hotpot_entangled.jsonl")
  printf '  %-10s uq=%-8s probes=%-9s judge=%s\n' "$KEY" "$u" "$p" "$j"
done

[ "${#failed[@]}" -eq 0 ] || exit 1
