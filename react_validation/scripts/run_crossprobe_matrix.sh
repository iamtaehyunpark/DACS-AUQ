#!/usr/bin/env bash
# Assessor x target P(True) matrix over result/pivot, off-diagonal only.
#
# Each assessor is served ONCE and probes every arm it did not generate, across both
# environments, then the server is torn down. Serving is the expensive part (a 70B load
# is minutes), so it is paid 5 times, not 45.
#
# The diagonal is not run: each arm's own probes.jsonl IS the self cell, produced during
# generation with the same probe code. Re-running it would duplicate, not add.
#
# P(True) only, deliberately. Intrinsic metrics (entropy / perplexity / sequence
# probability) are defined on a model's OWN generation — the distribution it sampled from,
# given its own prefix. Off-diagonal there is no such object: scoring another model's
# tokens is a relational quantity between the two models, which is the wrong shape for an
# instrument whose whole claim is that its readings do not depend on the target. P(True)
# is an elicited judgment ABOUT the step, so it means the same thing regardless of who
# generated it. The self/cross asymmetry is the thesis, not a gap to fill.
#
# RESUMABLE at (target x pass x shard) granularity — see run_hotpot_arm.sh for the same
# scheme. A dead server costs one shard.
#
# Usage: run_crossprobe_matrix.sh [SHARDS=8] [CONCURRENCY=8]
#   XP_ASSESSORS="Qwen3.6-35B-A3B ..."   restrict/reorder assessors
#   XP_DATASETS="alfworld hotpotqa"      restrict datasets
set -uo pipefail

RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=${XP_PY:-/opt/anaconda3/envs/Jagent/bin/python}
V=${XP_VLLM:-/opt/anaconda3/envs/yllm/bin/vllm}
PORT=${XP_PORT:-8092}
SHARDS=${1:-8}
CONC=${2:-8}
# Client-side concurrency is the real throughput limit, not the server: at SHARDS=8 the
# engine reported "Running: 4-5 reqs" against a 64-seq capacity, i.e. coasting. More
# shards = more in-flight requests. NOTE shard count is baked into the .done marker
# names, so changing it orphans existing markers and re-probes finished cells — only
# change it for an assessor with no completed cells.
MAX_NUM_SEQS=${XP_MAX_NUM_SEQS:-64}
PIVOT=$RD/result/pivot
OUTROOT=$PIVOT/crossprobe

HUB=/data3/hg_weight/hg_weight
export HF_HUB_CACHE=$HUB
export HF_HUB_OFFLINE=1

# Assessors are the five local models. deepseek-v4-flash is API-only and excluded here;
# it is a target, not an assessor.
ASSESSORS=${XP_ASSESSORS:-"Phi-4-mini-instruct gemma-3-4b-it Mistral-7B-Instruct-v0.3 Qwen3.6-35B-A3B Llama-3.3-70B-Instruct"}
DATASETS=${XP_DATASETS:-"alfworld hotpotqa"}

snap_for() {
  case "$1" in
    Phi-4-mini-instruct)      echo "$HUB/models--microsoft--Phi-4-mini-instruct/snapshots/5889daf2bc85b5300eba142a516fe65b0c2ef3f7" ;;
    gemma-3-4b-it)            echo "$HUB/models--google--gemma-3-4b-it/snapshots/093f9f388b31de276ce2de164bdc2081324b9767" ;;
    Mistral-7B-Instruct-v0.3) echo "$HUB/models--mistralai--Mistral-7B-Instruct-v0.3/snapshots/83e9aa141f2e28c82232fea5325f54edf17c43de" ;;
    Llama-3.3-70B-Instruct)   echo "$HUB/models--meta-llama--Llama-3.3-70B-Instruct/snapshots/6f6073b423013f6a7d4d9f39144961bfbfbc386b" ;;
    Qwen3.6-35B-A3B)          echo "Qwen/Qwen3.6-35B-A3B" ;;
  esac
}
tp_for()   { case "$1" in Llama-3.3-70B-Instruct) echo 2 ;; *) echo 1 ;; esac; }
util_for() { case "$1" in Llama-3.3-70B-Instruct|Qwen3.6-35B-A3B) echo 0.90 ;; *) echo 0.30 ;; esac; }
need_for() { case "$1" in Llama-3.3-70B-Instruct|Qwen3.6-35B-A3B) echo 78000 ;; *) echo 28000 ;; esac; }
gpus_for() { case "$1" in Llama-3.3-70B-Instruct) echo "${XP_GPU_BIG:-3,4}" ;; *) echo "${XP_GPU_SMALL:-4}" ;; esac; }

n_alive() { local c=0 p; for p in "$@"; do kill -0 "$p" 2>/dev/null && c=$((c+1)); done; echo "$c"; }

echo "crossprobe matrix start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "assessors: $ASSESSORS"
echo "datasets:  $DATASETS   shards=$SHARDS concurrency=$CONC max_num_seqs=$MAX_NUM_SEQS"

for ASSESSOR in $ASSESSORS; do
  SNAP=$(snap_for "$ASSESSOR"); TP=$(tp_for "$ASSESSOR")
  UTIL=$(util_for "$ASSESSOR"); NEED=$(need_for "$ASSESSOR"); GPU=$(gpus_for "$ASSESSOR")
  [ -n "$SNAP" ] || { echo "unknown assessor $ASSESSOR" >&2; continue; }

  # Is there any work left for this assessor? If every shard of every target is done,
  # skip without paying to load weights (a 70B load is minutes).
  todo_any=0
  for DS in $DATASETS; do
    for TDIR in "$PIVOT/$DS"/*/; do
      TARGET=$(basename "$TDIR")
      [ "$TARGET" = "$ASSESSOR" ] && continue
      [ -s "$TDIR/uq.jsonl" ] || continue
      for PASS in stages response; do
        for w in $(seq 0 $((SHARDS-1))); do
          [ -e "$OUTROOT/$DS/$TARGET/.$PASS.$ASSESSOR.w$w.done" ] || todo_any=1
        done
      done
    done
  done
  if [ "$todo_any" -eq 0 ]; then
    echo; echo "=== $ASSESSOR: all cells complete, skipping ==="; continue
  fi

  # Llama-70B is ~132GB of weights. At TP=2 that is ~66GB/card, which does not fit when
  # another user holds ~16GB of an 80GB card. Spread wider instead of failing: TP=4 puts
  # ~33GB on each card. Chosen from live free memory, not assumed.
  if [ "$ASSESSOR" = "Llama-3.3-70B-Instruct" ] && [ -z "${XP_GPU_BIG:-}" ]; then
    mapfile -t FREEG < <(nvidia-smi --query-gpu=index,memory.used,memory.total \
      --format=csv,noheader,nounits | awk -F', ' '{print $1" "($3-$2)}' | sort -k2 -nr)
    twofree=$(printf '%s\n' "${FREEG[@]}" | awk '$2>=70000' | wc -l)
    if [ "$twofree" -ge 2 ]; then
      GPU=$(printf '%s\n' "${FREEG[@]}" | awk '$2>=70000{print $1}' | head -2 | paste -sd, -)
      TP=2; UTIL=0.90
    else
      GPU=$(printf '%s\n' "${FREEG[@]}" | awk '$2>=40000{print $1}' | head -4 | paste -sd, -)
      n=$(echo "$GPU" | tr ',' '\n' | grep -c .)
      if [ "$n" -lt 4 ]; then
        echo "$ASSESSOR: need 4 GPUs with 40GB free (have $n) — skipping" >&2
        continue
      fi
      TP=4; UTIL=0.55
    fi
  fi

  echo; echo "================ assessor: $ASSESSOR (tp=$TP gpu=$GPU) ================"
  for prt in 8090 8091 8092 8093; do pgrep -f "vllm serve.*--port $prt" >/dev/null 2>&1 && pkill -f "vllm serve.*--port $prt"; done
  sleep 10

  SERVE_LOG=/tmp/xp_serve_${ASSESSOR}.log
  : > "$SERVE_LOG"
  EXTRA=""
  # Qwen lives in a different cache. HF_HUB_CACHE takes precedence over HF_HOME, so
  # setting HF_HOME alone leaves the resolver looking in /data3 and it fails with
  # LocalEntryNotFoundError under HF_HUB_OFFLINE. Point BOTH at the right place.
  if [ "$ASSESSOR" = "Qwen3.6-35B-A3B" ]; then
    export HF_HOME=/data5/user/hf_cache HF_HUB_CACHE=/data5/user/hf_cache/hub
  else
    export HF_HUB_CACHE=$HUB
  fi
  if [ "$TP" -gt 1 ]; then
    export NCCL_NET_PLUGIN=none NCCL_IB_DISABLE=1 NCCL_SOCKET_IFNAME=lo VLLM_HOST_IP=127.0.0.1
  fi
  CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve "$SNAP" --served-model-name qwen \
    --tensor-parallel-size "$TP" --max-model-len 16384 \
    --gpu-memory-utilization "$UTIL" --max-num-seqs "$MAX_NUM_SEQS" \
    --port "$PORT" >> "$SERVE_LOG" 2>&1 &
  SRV=$!
  echo -n "serving"
  up=0
  for _ in $(seq 1 240); do
    curl -sf "http://localhost:$PORT/v1/models" >/dev/null 2>&1 && { up=1; echo " up"; break; }
    kill -0 $SRV 2>/dev/null || break
    echo -n .; sleep 5
  done
  if [ "$up" -ne 1 ]; then
    echo; echo "$ASSESSOR: SERVE FAILED — see $SERVE_LOG; continuing to next assessor" >&2
    tail -5 "$SERVE_LOG" >&2
    continue
  fi

  # Probe settings match the banked cross-probe runs so old and new cells are comparable.
  # P(True) reads first-token logprob mass, which is temperature-invariant, but the
  # sampling config is part of the recipe and is pinned rather than left to defaults.
  export PROBE_MODEL=qwen PROBE_TOKENIZER=$SNAP PROBE_BASE_URL=http://localhost:$PORT/v1
  export PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0
  unset UQ_API_MODE UQ_RPM UQ_RATE_FILE PROBE_API_KEY
  cd "$RD/src"

  for DS in $DATASETS; do
    for TDIR in "$PIVOT/$DS"/*/; do
      TARGET=$(basename "$TDIR")
      [ "$TARGET" = "$ASSESSOR" ] && continue          # diagonal = the arm's own probes.jsonl
      UQ=$TDIR/uq.jsonl
      [ -s "$UQ" ] || { echo "  skip $DS/$TARGET (no uq.jsonl)"; continue; }
      OUT=$OUTROOT/$DS/$TARGET
      mkdir -p "$OUT"

      for PASS in stages response; do
        case "$PASS" in
          stages)   STAGE_ARG="thought,action"; RESP_ARG="" ;;
          response) STAGE_ARG="";               RESP_ARG="ptrue" ;;
        esac
        pend=()
        for w in $(seq 0 $((SHARDS-1))); do
          [ -e "$OUT/.$PASS.$ASSESSOR.w$w.done" ] && continue
          rm -f "$OUT/ptrue.$ASSESSOR.$PASS.w$w.jsonl"
          pend+=("$w")
        done
        if [ "${#pend[@]}" -eq 0 ]; then echo "  $DS/$TARGET [$PASS] done"; continue; fi
        echo "  $DS/$TARGET [$PASS] shards: ${pend[*]}"
        pids=()
        for w in "${pend[@]}"; do
          while [ "$(n_alive ${pids[@]+"${pids[@]}"})" -ge "$CONC" ]; do sleep 2; done
          (
            PROBE_INPUT="$UQ" PROBE_OUTPUT="$OUT/ptrue.$ASSESSOR.$PASS.w$w.jsonl" \
            PROBE_NUM_WORKERS=$SHARDS PROBE_WORKER_ID=$w \
            PROBE_KINDS=ptrue PROBE_STAGES="$STAGE_ARG" PROBE_RESPONSE_KINDS="$RESP_ARG" \
              $PY -u run_probes.py > "$OUT/ptrue.$ASSESSOR.$PASS.w$w.log" 2>&1 \
              && touch "$OUT/.$PASS.$ASSESSOR.w$w.done"
          ) &
          pids+=($!)
        done
        for p in ${pids[@]+"${pids[@]}"}; do wait "$p" || true; done
        done_n=$(ls "$OUT/.$PASS.$ASSESSOR.w"*.done 2>/dev/null | wc -l)
        if [ "$done_n" -eq "$SHARDS" ]; then
          cat "$OUT/ptrue.$ASSESSOR.$PASS.w"*.jsonl > "$OUT/ptrue.$ASSESSOR.$PASS.jsonl"
          echo "    merged -> ptrue.$ASSESSOR.$PASS.jsonl ($(wc -l < "$OUT/ptrue.$ASSESSOR.$PASS.jsonl") records)"
        else
          echo "    INCOMPLETE $done_n/$SHARDS shards — re-run to resume" >&2
        fi
      done
    done
  done

  kill -- -"$(ps -o pgid= $SRV 2>/dev/null | tr -d ' ')" 2>/dev/null
  pkill -f "vllm serve.*--port $PORT" 2>/dev/null
  sleep 10
  echo "$ASSESSOR: server down"
done

echo; echo "================ matrix summary ================"
for DS in $DATASETS; do
  for TDIR in "$PIVOT/$DS"/*/; do
    TARGET=$(basename "$TDIR")
    n=$(ls "$OUTROOT/$DS/$TARGET"/ptrue.*.stages.jsonl 2>/dev/null | wc -l)
    printf '  %-9s %-26s assessors with merged stages output: %s\n' "$DS" "$TARGET" "$n"
  done
done
echo "done $(date -u +%Y-%m-%dT%H:%M:%SZ)"
