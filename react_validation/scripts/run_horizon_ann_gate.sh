#!/bin/bash
# QUEUED JOB: wait for ANY GPU to free, then run the P(True) context x rule probe on
# Qwen3.6-35B-A3B. Scans all 5 cards every poll and takes the first one with enough room —
# whichever frees first wins, instead of holding out for one specific card.
#
# "Free" = >=74000 MiB actually free, which is what a 35B at util 0.90 needs. We do NOT kill
# anything to get there (user2 has jobs on every card); we just wait our turn.
#
#   selection (GPU-free, done immediately) -> wait for any GPU -> serve qwen -> 20 steps x 11
#   conditions -> free the GPU -> markdown + matrix CSV.
#
# Outputs in result/ctxrule/. Idempotent: the sweep output is removed before the run (run_* appends).
set -u
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
V=/opt/anaconda3/envs/yllm/bin/vllm
SNAP=/data5/user/hf_cache/hub/models--Qwen--Qwen3.6-35B-A3B/snapshots/995ad96eacd98c81ed38be0c5b274b04031597b0
OUT=$RD/result/ctxrule
PORT=8043
GPU=                    # chosen at run time by the scan below
# vLLM at util 0.90 demands 71.33 GiB = ~73043 MiB free AT ITS OWN STARTUP, ~20s after we look.
# 74000 left almost no slack and the first run lost that race. 78000 = a near-empty card.
NEED_MIB=78000
POLL=60
MAX_WAIT_H=48

CORPUS_UQ=$RD/result/e1/e1b/uq_entangled_e1.jsonl
CORPUS_JUDGE=$RD/result/e1/e1b/judge_entangled_e1.jsonl
SEL=$OUT/sel_horizon2.json
REC=$OUT/ptrue_horizon_ann_e1b.jsonl

cd $RD
export ALFWORLD_DATA=/home/user/.cache/alfworld HF_HUB_OFFLINE=1 HF_HOME=/data5/user/hf_cache
unset UQ_API_MODE UQ_MIN_INTERVAL UQ_RPM UQ_RATE_FILE REACT_API_KEY PROBE_API_KEY
mkdir -p $OUT

echo "=== [ctxrule] START $(date) ==="

# ---- 1. selection: no GPU needed, so do it now and fail fast if the corpus join is broken
[ -s "$SEL" ] || { echo "SELECTION_MISSING $SEL — run the select step first"; exit 1; }
NSEL=$($PY -c "import json;print(len(json.load(open('$SEL'))['steps']))")
echo "[ctxrule] selection ready: $NSEL steps -> $SEL"

# ---- 2. wait for ANY GPU. Never kill another user's job to get one.
echo "[ctxrule] waiting for any GPU to reach ${NEED_MIB}MiB free (poll ${POLL}s, giving up after ${MAX_WAIT_H}h)"
deadline=$(( $(date +%s) + MAX_WAIT_H * 3600 ))
last_report=0

pick_gpu() {    # echo the index of the first card with >= NEED_MIB free, or nothing
  nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits 2>/dev/null |
  while IFS=', ' read -r idx free; do
    case "$free" in ''|*[!0-9]*) continue ;; esac
    [ "$free" -ge "$NEED_MIB" ] && { echo "$idx"; break; }
  done
}

wait_for_gpu() {    # block until a card has room; sets GPU. Returns 1 only on the global deadline.
  while :; do
    GPU=$(pick_gpu)
    if [ -n "$GPU" ]; then
      # Settle, then RE-CHECK: between the scan and the serve another user can claim the card.
      echo "[ctxrule] candidate GPU$GPU free at $(date) — settling 20s"
      sleep 20
      recheck=$(nvidia-smi --id=$GPU --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null)
      case "$recheck" in ''|*[!0-9]*) recheck=0 ;; esac
      if [ "$recheck" -ge "$NEED_MIB" ]; then
        echo "[ctxrule] TAKING GPU$GPU (${recheck}MiB free)"
        return 0
      fi
      echo "[ctxrule] GPU$GPU was taken during settle (${recheck}MiB) — back to waiting"
      GPU=
    fi
    if [ "$(date +%s)" -ge "$deadline" ]; then
      echo "[ctxrule] GAVE_UP after ${MAX_WAIT_H}h — no GPU ever freed"
      nvidia-smi --query-gpu=index,memory.free --format=csv,noheader
      return 1
    fi
    now=$(date +%s)
    if [ $(( now - last_report )) -ge 1800 ]; then    # heartbeat every 30 min, not every minute
      echo "[ctxrule] $(date +%H:%M) still waiting | free MiB: $(nvidia-smi --query-gpu=memory.free \
        --format=csv,noheader,nounits | tr '\n' ' ')"
      last_report=$now
    fi
    sleep $POLL
  done
}

# ---- 3. serve, WITH RETRY. The previous run died here: the gate saw >=74000MiB, passed its
#         re-check, and then lost ~10GiB to another process during vLLM's own startup —
#         "Free memory on device cuda:0 (61.5/79.26 GiB) ... less than desired (0.9, 71.33 GiB)".
#         On a box shared with jobs that cycle every few minutes, a failed serve is a NORMAL
#         event, not a fatal one: clean up and go back to waiting for a card.
#         Qwen3.6-35B-A3B is hybrid Mamba: --max-num-seqs must stay <=130 or CUDA-graph capture
#         aborts on Mamba cache blocks (memory: server-env / llama70b run).
MAX_ATTEMPTS=20
SRV=
FREED=0
free_gpu() {
  [ "$FREED" = 1 ] && return 0            # idempotent: trap + explicit call must not double-kill
  FREED=1
  SPGID=$(ps -o pgid= -p $SRV 2>/dev/null | tr -d ' ')
  if [ -n "$SPGID" ] && [ "$SPGID" != "$(ps -o pgid= -p $$ | tr -d ' ')" ]; then kill -9 -$SPGID 2>/dev/null; fi
  # Match on OUR PORT, not on "served-model-name qwen": other jobs on this box have served a
  # model under that same name (the hotpot gate used qwen on :8000), and a name-based pkill
  # would take theirs down with ours. Port 8040 belongs to this script alone.
  pkill -9 -f -- "--port $PORT" 2>/dev/null
  sleep 8
  echo "=== [ctxrule] GPU$GPU freed $(date) ==="
}
# EXIT covers a normal end and any error path; INT/TERM cover `systemctl stop` and a manual
# kill. Without the signal traps, stopping the job would strand a 70GB vLLM on the card.
trap free_gpu EXIT INT TERM

attempt=0
while :; do
  attempt=$(( attempt + 1 ))
  [ "$attempt" -gt "$MAX_ATTEMPTS" ] && { echo "[ctxrule] GAVE_UP after $MAX_ATTEMPTS serve attempts"; exit 3; }
  wait_for_gpu || exit 2
  echo "[ctxrule] serve attempt $attempt/$MAX_ATTEMPTS on GPU$GPU $(date)"

  : > /tmp/horizon_ann_serve.log
  CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve "$SNAP" --served-model-name qwen \
    --tensor-parallel-size 1 --max-model-len 16384 \
    --gpu-memory-utilization 0.90 --max-num-seqs 128 \
    --port $PORT >> /tmp/horizon_ann_serve.log 2>&1 &
  SRV=$!
  ready=0
  for i in $(seq 1 180); do
    curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 && { ready=1; break; }
    grep -qiE "Engine core initialization failed|out of memory|ValueError|Error in inspecting model" \
      /tmp/horizon_ann_serve.log 2>/dev/null && break
    kill -0 $SRV 2>/dev/null || break                # server died outright
    sleep 10
  done
  [ "$ready" = 1 ] && { echo "[ctxrule] SERVER_READY on GPU$GPU $(date)"; break; }

  echo "[ctxrule] serve attempt $attempt FAILED on GPU$GPU:"
  grep -m2 -E "ValueError|out of memory|Engine core initialization failed" /tmp/horizon_ann_serve.log | cut -c1-200
  cp /tmp/horizon_ann_serve.log /tmp/horizon_ann_serve.attempt$attempt.log 2>/dev/null
  FREED=0; free_gpu; FREED=0        # tear down the half-started server, then try again
  sleep 60
done

# ---- 4. sweep: 120 steps x 7 horizons = 840 single-token calls, 7 in flight
rm -f $REC
$PY -u src/ptrue_horizon_probe.py run \
  --selection $SEL --out $REC \
  --model qwen --tokenizer "$SNAP" --base-url http://localhost:$PORT/v1 --concurrency 21 --annotate none,agent,ptrue \
  > $OUT/run_horizon_ann.log 2>&1
rc=$?
echo "[ctxrule] sweep rc=$rc lines=$(wc -l < $REC 2>/dev/null || echo 0)"
tail -3 $OUT/run_horizon_ann.log

# Free the card the moment the sweep is done — the report needs no GPU, so nothing below this
# line should hold 70GB while it renders markdown.
free_gpu; trap - EXIT INT TERM
nvidia-smi --id=$GPU --query-gpu=index,memory.free --format=csv,noheader

# ---- 5. report (no GPU)
$PY -u src/ptrue_horizon_probe.py report \
  --records $REC --csv $OUT/ptrue_horizon_ann_e1b_curves.csv --out $OUT/ptrue_horizon_ann_e1b.md
echo "CTXRULE_DONE $(date)"
echo "--- separation table ---"
sed -n '/## Trajectory outcome/,/^$/p;/^| /p' $OUT/ptrue_horizon_ann_e1b.md | head -40
