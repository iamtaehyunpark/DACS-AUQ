#!/bin/bash
# CROSS-MODEL P(True): Qwen3.6-35B-A3B evaluates MISTRAL-7B's frozen entangled trajectories.
#
# Fills the gap left by run_crossprobe_qwen.sh, which covered {decoupled,entangled} x
# {phi4mini,gemma4b} — the mistral entangled run only finished afterwards (2026-07-30 15:34).
#
# Question (same as the original cross-probe): when a small model shows poor P(True) AUROC, is
# that because its TRAJECTORIES are degenerate (generator problem) or because it cannot
# SELF-ASSESS (evaluator problem)? Holding the trajectories fixed and swapping only the evaluator
# separates the two. run_probes.py never re-runs the agent — it reconstructs (task, history,
# commands, thought, action) from the frozen uq log and issues fresh probe calls to PROBE_MODEL.
#
# P(True) ONLY: no posthoc_numeric, no sep_verbalized, no targeted.
#
# Corpus: result/models4/uq_entangled_mistral7b.jsonl — 140 episodes, 6482 steps, and
# judge_entangled_mistral7b.jsonl has 6482 labels, so the join is complete.
#   6482 steps x 2 stages (thought,action) + 6482 (response) = ~19.4k single-token calls.
set -u
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
V=/opt/anaconda3/envs/yllm/bin/vllm
OUT=$RD/result/models4
QWEN=Qwen/Qwen3.6-35B-A3B
TAG=entangled_mistral7b
PORT=8044
GPU=
NEED_MIB=78000
POLL=60
MAX_WAIT_H=48
MAX_ATTEMPTS=20

cd $RD
export HF_HOME=/data5/user/hf_cache HF_HUB_OFFLINE=1
unset UQ_API_MODE UQ_RPM UQ_MIN_INTERVAL UQ_RATE_FILE REACT_API_KEY PROBE_API_KEY

uq=$OUT/uq_${TAG}.jsonl
[ -s "$uq" ] || { echo "MISSING $uq"; exit 1; }
echo "=== [xp-mistral] START $(date) | $(grep -c '"kind": "step"' $uq) steps ==="

pick_gpu() {
  nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits 2>/dev/null |
  while IFS=', ' read -r idx free; do
    case "$free" in ''|*[!0-9]*) continue ;; esac
    [ "$free" -ge "$NEED_MIB" ] && { echo "$idx"; break; }
  done
}

deadline=$(( $(date +%s) + MAX_WAIT_H * 3600 ))
last_report=0
wait_for_gpu() {
  while :; do
    GPU=$(pick_gpu)
    if [ -n "$GPU" ]; then
      echo "[xp] candidate GPU$GPU free — settling 20s"
      sleep 20
      recheck=$(nvidia-smi --id=$GPU --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null)
      case "$recheck" in ''|*[!0-9]*) recheck=0 ;; esac
      [ "$recheck" -ge "$NEED_MIB" ] && { echo "[xp] TAKING GPU$GPU (${recheck}MiB)"; return 0; }
      echo "[xp] GPU$GPU taken during settle — back to waiting"
      GPU=
    fi
    [ "$(date +%s)" -ge "$deadline" ] && { echo "[xp] GAVE_UP after ${MAX_WAIT_H}h"; return 1; }
    now=$(date +%s)
    if [ $(( now - last_report )) -ge 1800 ]; then
      echo "[xp] $(date +%H:%M) waiting | free MiB: $(nvidia-smi --query-gpu=memory.free \
        --format=csv,noheader,nounits | tr '\n' ' ')"
      last_report=$now
    fi
    sleep $POLL
  done
}

SRV=
FREED=0
free_gpu() {
  [ "$FREED" = 1 ] && return 0
  FREED=1
  SPGID=$(ps -o pgid= -p $SRV 2>/dev/null | tr -d ' ')
  if [ -n "$SPGID" ] && [ "$SPGID" != "$(ps -o pgid= -p $$ | tr -d ' ')" ]; then kill -9 -$SPGID 2>/dev/null; fi
  # Match on OUR PORT, not "served-model-name qwen" (which run_crossprobe_qwen.sh used): other
  # jobs on this box serve under that same name and a name-based pkill would take theirs down.
  pkill -9 -f -- "--port $PORT" 2>/dev/null
  sleep 8
  echo "=== [xp] GPU$GPU freed $(date) ==="
}
trap free_gpu EXIT INT TERM

attempt=0
while :; do
  attempt=$(( attempt + 1 ))
  [ "$attempt" -gt "$MAX_ATTEMPTS" ] && { echo "[xp] GAVE_UP after $MAX_ATTEMPTS serve attempts"; exit 3; }
  wait_for_gpu || exit 2
  echo "[xp] serve attempt $attempt/$MAX_ATTEMPTS on GPU$GPU $(date)"
  : > /tmp/xp_mistral_serve.log
  CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve $QWEN --served-model-name qwen \
    --tensor-parallel-size 1 --max-model-len 16384 \
    --gpu-memory-utilization 0.90 --max-num-seqs 128 \
    --port $PORT >> /tmp/xp_mistral_serve.log 2>&1 &
  SRV=$!
  ready=0
  for i in $(seq 1 180); do
    curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 && { ready=1; break; }
    grep -qiE "Engine core initialization failed|out of memory|ValueError" /tmp/xp_mistral_serve.log 2>/dev/null && break
    kill -0 $SRV 2>/dev/null || break
    sleep 10
  done
  [ "$ready" = 1 ] && { echo "[xp] QWEN_READY on GPU$GPU $(date)"; break; }
  echo "[xp] serve attempt $attempt FAILED:"
  grep -m2 -E "ValueError|out of memory|Engine core initialization failed" /tmp/xp_mistral_serve.log | cut -c1-200
  FREED=0; free_gpu; FREED=0
  sleep 60
done

xprobe() {   # stages  suffix
  stages=$1; sfx=$2
  out=$OUT/probes_${TAG}.qwenjudge${sfx}.jsonl
  rm -f ${out%.jsonl}.w*.jsonl $out
  pids=()
  for w in 0 1 2 3 4 5 6 7; do
    PROBE_INPUT=$uq PROBE_OUTPUT=${out%.jsonl}.w${w}.jsonl \
      PROBE_NUM_WORKERS=8 PROBE_WORKER_ID=$w \
      PROBE_BASE_URL=http://localhost:$PORT/v1 PROBE_MODEL=qwen PROBE_TOKENIZER=$QWEN \
      PROBE_KINDS=ptrue PROBE_STAGES="$stages" PROBE_RESPONSE_KINDS="" \
      PROBE_TEMPERATURE=0 PROBE_TOP_P=1.0 PROBE_PRESENCE_PENALTY=0 PROBE_REPETITION_PENALTY=1.0 \
      $PY -u src/run_probes.py > ${out%.jsonl}_w${w}.log 2>&1 &
    pids+=($!)
  done
  wait "${pids[@]}"
  cat ${out%.jsonl}.w*.jsonl > $out
  echo "XP_DONE ${TAG}${sfx} stages=$stages records=$(wc -l < $out) $(date)"
}

xprobe "thought,action" ""
xprobe "response"       ".aggtrue_ptrue"

free_gpu; trap - EXIT INT TERM
echo "XP_ALL_DONE $(date)"
for f in $OUT/probes_${TAG}.qwenjudge.jsonl $OUT/probes_${TAG}.qwenjudge.aggtrue_ptrue.jsonl; do
  [ -s "$f" ] && echo "  $(basename $f): $(wc -l < $f) records, parse_ok $(grep -c '"parse_ok": true' $f)"
done
