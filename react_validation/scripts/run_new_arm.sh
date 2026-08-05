#!/usr/bin/env bash
# Full generation chain for one agent model, both environments, straight into the pivot.
#
# Per (model x dataset) it produces the four artifacts a cell needs:
#   uq.jsonl              entangled trajectories + logprobs + in-generation confidence
#   probes.jsonl          post-hoc probes over thought/action
#   probes.aggtrue.jsonl  whole-response P(True)
#   judge.jsonl           3-judge ensemble step labels (Azure, no GPU)
#
# Generation and probing share one serving window because the probes read the AGENT's
# own logprobs. The judge is Azure-side and runs after the server is down, so the GPU
# is released as early as possible.
#
# Written directly to result/pivot/<dataset>/<exact model name>/ so a new arm needs no
# reorganisation step afterwards. Model directory names use the upstream name.
#
# RESUMABLE at cell and shard level: a finished artifact is skipped, and within a phase
# only shards without a .done marker are (re)run. A partial shard is discarded rather
# than continued, because neither the generator nor run_probes.py skips completed work —
# both append blindly, so resuming inside a shard would duplicate records.
#
# Usage: run_new_arm.sh <model_key> [DATASETS="alfworld hotpotqa"] [SHARDS=8] [CONC=8]
#   model_key: qwen35-4b | qwen35-9b | qwen35-27b
set -uo pipefail

RD="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY=${ARM_PY:-/opt/anaconda3/envs/Jagent/bin/python}
V=${ARM_VLLM:-/opt/anaconda3/envs/yllm/bin/vllm}
PORT=${ARM_PORT:-8081}
KEY=${1:?usage: run_new_arm.sh <model_key> [DATASETS] [SHARDS] [CONC]}
DATASETS=${2:-"alfworld hotpotqa"}
SHARDS=${3:-8}
CONC=${4:-8}

export HF_HUB_OFFLINE=1
export ALFWORLD_DATA=${ALFWORLD_DATA:-/home/user/.cache/alfworld}

# Qwen3.5-4B and -9B live in the /data5 cache next to Qwen3.6-35B; the 27B is in the
# user's own HF cache. HF_HUB_CACHE must point at the right hub dir per model, since it
# takes precedence over HF_HOME and offline mode turns a miss into a hard failure.
case "$KEY" in
  qwen35-4b)
    MODEL=Qwen3.5-4B;  HUB=/data5/user/hf_cache/hub
    SNAP=$HUB/models--Qwen--Qwen3.5-4B/snapshots/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a
    UTIL=0.30; NEED=28000 ;;
  qwen35-9b)
    MODEL=Qwen3.5-9B;  HUB=/data5/user/hf_cache/hub
    SNAP=$HUB/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a
    UTIL=0.40; NEED=38000 ;;
  qwen35-27b)
    MODEL=Qwen3.5-27B; HUB=/home/user/.cache/huggingface/hub
    SNAP=$HUB/models--Qwen--Qwen3.5-27B/snapshots/fc05daec18b0a78c049392ed2e771dde82bdf654
    UTIL=0.80; NEED=70000 ;;
  *) echo "unknown model key: $KEY (qwen35-4b|qwen35-9b|qwen35-27b)" >&2; exit 1 ;;
esac
export HF_HUB_CACHE=$HUB
[ -d "$SNAP" ] || { echo "snapshot missing: $SNAP" >&2; exit 1; }

# Episode counts match the existing arms so the new cells are directly comparable:
# ALFWorld 140 episodes (~6.5k steps), HotpotQA 500 (~2.5k steps).
ALF_EPISODES=${ARM_ALF_EPISODES:-140}
HOT_EPISODES=${ARM_HOT_EPISODES:-500}

n_alive() { local c=0 p; for p in "$@"; do kill -0 "$p" 2>/dev/null && c=$((c+1)); done; echo "$c"; }

# Run pending shards of one phase, at most CONC at a time. A bare `wait` would also
# block on the vLLM server, which is a background child of this shell and never exits.
run_shards() {
  local sh=$1 prefix=$2; shift 2
  local todo=() w p rc=0
  for w in $(seq 0 $((SHARDS-1))); do
    [ -e "$sh/$prefix.w$w.done" ] && continue
    rm -f "$sh/$prefix.w$w.jsonl"
    todo+=("$w")
  done
  [ "${#todo[@]}" -eq 0 ] && { echo "    all $SHARDS shards done"; return 0; }
  echo "    shards: ${todo[*]}"
  local pids=()
  for w in "${todo[@]}"; do
    while [ "$(n_alive ${pids[@]+"${pids[@]}"})" -ge "$CONC" ]; do sleep 2; done
    ( "$@" "$w" && touch "$sh/$prefix.w$w.done" ) &
    pids+=($!)
  done
  for p in ${pids[@]+"${pids[@]}"}; do wait "$p" || rc=1; done
  return $rc
}

echo "=== arm $MODEL ($KEY) datasets: $DATASETS shards=$SHARDS conc=$CONC ==="
echo "snapshot=$SNAP"

for DS in $DATASETS; do
  CELL=$RD/result/pivot/$DS/$MODEL
  SH=$CELL/shards
  mkdir -p "$SH"
  UQ=$CELL/uq.jsonl; PROBES=$CELL/probes.jsonl
  AGG=$CELL/probes.aggtrue.jsonl; JUDGE=$CELL/judge.jsonl

  if [ -s "$UQ" ] && [ -s "$PROBES" ] && [ -s "$AGG" ] && [ -s "$JUDGE" ]; then
    echo; echo "--- $DS/$MODEL: complete, skipping ---"; continue
  fi
  echo; echo "--- $DS/$MODEL ---"

  case "$DS" in
    alfworld) GEN=chat_react_hotpot_entangled.py ;;   # overridden below
  esac
  if [ "$DS" = alfworld ]; then
    GEN=chat_react_entangled.py; EPISODES=$ALF_EPISODES; SPLIT=eval_in_distribution
    PROBE_KINDS_MAIN="ptrue,sep_verbalized,posthoc_numeric,targeted"; JUDGE_PY=judge_e0.py
  else
    GEN=chat_react_hotpot_entangled.py; EPISODES=$HOT_EPISODES; SPLIT=dev
    # entangled HotpotQA excludes the targeted q_t probe by design
    PROBE_KINDS_MAIN="ptrue,sep_verbalized,posthoc_numeric"; JUDGE_PY=judge_hotpot.py
  fi

  # ---- serve (generation + probes share this window) ----
  if [ ! -s "$UQ" ] || [ ! -s "$PROBES" ] || [ ! -s "$AGG" ]; then
    mapfile -t FREE < <(nvidia-smi --query-gpu=index,memory.used,memory.total \
      --format=csv,noheader,nounits | awk -F', ' -v n="$NEED" '($3-$2)>=n {print $1}')
    if [ -n "${ARM_GPU:-}" ]; then GPU=$ARM_GPU
    elif [ "${#FREE[@]}" -ge 1 ]; then GPU=${FREE[0]}
    else echo "  no GPU with ${NEED}MiB free — skipping $DS" >&2; continue; fi
    echo "  gpu=$GPU util=$UTIL"

    pgrep -f "vllm serve.*--port $PORT" >/dev/null 2>&1 && { pkill -f "vllm serve.*--port $PORT"; sleep 10; }
    SERVE_LOG=$CELL/serve.log; : > "$SERVE_LOG"
    CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve "$SNAP" --served-model-name qwen \
      --tensor-parallel-size 1 --max-model-len 16384 \
      --gpu-memory-utilization "$UTIL" --max-num-seqs 64 \
      --port "$PORT" >> "$SERVE_LOG" 2>&1 &
    SRV=$!
    echo -n "  serving"
    up=0
    for _ in $(seq 1 240); do
      curl -sf "http://localhost:$PORT/v1/models" >/dev/null 2>&1 && { up=1; echo " up"; break; }
      kill -0 $SRV 2>/dev/null || break
      echo -n .; sleep 5
    done
    [ "$up" -eq 1 ] || { echo; echo "  SERVE FAILED for $DS — see $SERVE_LOG" >&2; tail -5 "$SERVE_LOG" >&2; continue; }

    export REACT_MODEL=qwen PROBE_MODEL=qwen
    export REACT_TOKENIZER=$SNAP PROBE_TOKENIZER=$SNAP
    export REACT_BASE_URL=http://localhost:$PORT/v1 PROBE_BASE_URL=http://localhost:$PORT/v1
    export REACT_TEMPERATURE=0.7 REACT_TOP_P=0.80 REACT_TOP_K=20 REACT_MIN_P=0.0
    export REACT_PRESENCE_PENALTY=1.5 REACT_REPETITION_PENALTY=1.0
    # "false" actively disables thinking via the chat template; "none" only OMITS the
    # kwarg, which is right for Phi/gemma (no such switch) but leaves Qwen thinking ON.
    # These are Qwen models and their smoke reply began with "Thinking Process:", which
    # would pollute the THOUGHT:/ACTION:/CONFIDENCE: format the parser expects.
    export REACT_ENABLE_THINKING=${ARM_ENABLE_THINKING:-false}
    export REACT_SPLIT=$SPLIT REACT_SEED=233 REACT_SEED_BASE=1000
    unset UQ_API_MODE UQ_RPM UQ_RATE_FILE REACT_API_KEY PROBE_API_KEY
    cd "$RD/src"

    gen_shard() {
      local w=$1
      REACT_N_EPISODES=$EPISODES REACT_NUM_WORKERS=$SHARDS REACT_WORKER_ID="$w" \
      REACT_RUN_ID="entangled_${MODEL}_${DS}" REACT_UQLOG="$SH/uq.w$w.jsonl" \
        $PY -u "$GEN" > "$SH/uq.w$w.log" 2>&1
    }
    probe_main() {
      local w=$1
      PROBE_INPUT="$UQ" PROBE_OUTPUT="$SH/probes.w$w.jsonl" \
      PROBE_NUM_WORKERS=$SHARDS PROBE_WORKER_ID="$w" \
      PROBE_KINDS="$PROBE_KINDS_MAIN" PROBE_STAGES="thought,action" PROBE_RESPONSE_KINDS="" \
      PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
        $PY -u run_probes.py > "$SH/probes.w$w.log" 2>&1
    }
    probe_agg() {
      local w=$1
      PROBE_INPUT="$UQ" PROBE_OUTPUT="$SH/agg.w$w.jsonl" \
      PROBE_NUM_WORKERS=$SHARDS PROBE_WORKER_ID="$w" \
      PROBE_KINDS="ptrue" PROBE_STAGES="" PROBE_RESPONSE_KINDS="ptrue" \
      PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
        $PY -u run_probes.py > "$SH/agg.w$w.log" 2>&1
    }

    if [ ! -s "$UQ" ]; then
      echo "  phase 1/3 generation ($EPISODES episodes)"
      run_shards "$SH" uq gen_shard && cat "$SH"/uq.w*.jsonl > "$UQ"
      echo "  uq.jsonl: $(wc -l < "$UQ" 2>/dev/null) records"
    fi
    if [ -s "$UQ" ] && [ ! -s "$PROBES" ]; then
      echo "  phase 2/3 probes (thought,action)"
      run_shards "$SH" probes probe_main && cat "$SH"/probes.w*.jsonl > "$PROBES"
      echo "  probes.jsonl: $(wc -l < "$PROBES" 2>/dev/null) records"
    fi
    if [ -s "$UQ" ] && [ ! -s "$AGG" ]; then
      echo "  phase 3/3 probes (whole response)"
      run_shards "$SH" agg probe_agg && cat "$SH"/agg.w*.jsonl > "$AGG"
      echo "  probes.aggtrue.jsonl: $(wc -l < "$AGG" 2>/dev/null) records"
    fi

    kill -- -"$(ps -o pgid= $SRV 2>/dev/null | tr -d ' ')" 2>/dev/null
    pkill -f "vllm serve.*--port $PORT" 2>/dev/null
    sleep 10
    echo "  server down, GPU released"
  fi

  # ---- judge: Azure, no GPU, so it runs after teardown ----
  if [ -s "$UQ" ] && [ ! -s "$JUDGE" ]; then
    JF=${AZURE_JUDGE_ENV_FILE:-$HOME/.config/azure_judge.env}
    if [ -r "$JF" ]; then
      # shellcheck disable=SC1090
      source "$JF"
      # gpt-5.6-sol can go direct to OpenAI instead of the Azure deployment; the other
      # two judges stay on Azure. Optional — absent file just means Azure for all three.
      OJF=${OPENAI_JUDGE_ENV_FILE:-$HOME/.config/openai_judge.env}
      # shellcheck disable=SC1090
      [ -r "$OJF" ] && source "$OJF"
      echo "  judging ($JUDGE_PY)"
      ( cd "$RD/src" && JUDGE_INPUT="$UQ" JUDGE_OUTPUT="$JUDGE" JUDGE_WORKERS=8 \
          $PY -u "$JUDGE_PY" > "$CELL/judge.log" 2>&1 )
      echo "  judge.jsonl: $(wc -l < "$JUDGE" 2>/dev/null) labels"
    else
      echo "  judge env unreadable ($JF) — skipped" >&2
    fi
  fi
done

echo
echo "=== $MODEL summary ==="
for DS in $DATASETS; do
  C=$RD/result/pivot/$DS/$MODEL
  printf '  %-9s uq=%-7s probes=%-8s agg=%-7s judge=%s\n' "$DS" \
    "$(wc -l < "$C/uq.jsonl" 2>/dev/null || echo 0)" \
    "$(wc -l < "$C/probes.jsonl" 2>/dev/null || echo 0)" \
    "$(wc -l < "$C/probes.aggtrue.jsonl" 2>/dev/null || echo 0)" \
    "$(wc -l < "$C/judge.jsonl" 2>/dev/null || echo 0)"
done
