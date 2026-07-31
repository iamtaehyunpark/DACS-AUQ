#!/bin/bash
# UNCERTAINTY-FEEDBACK INTERVENTION: re-run originally-failed episodes with P(True) written back
# into the agent's context. Qwen3.6-35B-A3B, entangled, ALFWorld + HotpotQA, 15 episodes each.
#
#   arms: control (plain retry) | prod (production P(True)) | c5 (P(True) with the outcome)
#   all three arms share the same seed schedule, so they are identical until the first annotation
#
# Order: wait for a GPU -> serve -> calibrate hotpot/c5 threshold -> ALFWorld 3 arms (parallel,
# sharded) -> HotpotQA 3 arms (parallel) -> free the GPU.
set -u
RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
PY=/opt/anaconda3/envs/Jagent/bin/python
V=/opt/anaconda3/envs/yllm/bin/vllm
SNAP=/data5/user/hf_cache/hub/models--Qwen--Qwen3.6-35B-A3B/snapshots/995ad96eacd98c81ed38be0c5b274b04031597b0
OUT=$RD/result/uqfb
PORT=8044
GPU=
NEED_MIB=78000
POLL=60
MAX_WAIT_H=48
MAX_ATTEMPTS=12
NWORK=5                    # stride-shard each ALFWorld arm across this many processes
# GPU0 served NaN logits for every request on 2026-07-31 (model loaded and captured CUDA graphs
# cleanly, then produced garbage; the box also logs RmInitAdapter failures for a 6th, dead card).
# Skip it by default, and — more importantly — CANARY every server before trusting it.
EXCLUDE_GPUS="${UQFB_EXCLUDE_GPUS:-}"

cd $RD
export ALFWORLD_DATA=/home/user/.cache/alfworld HF_HUB_OFFLINE=1 HF_HOME=/data5/user/hf_cache
unset UQ_API_MODE UQ_MIN_INTERVAL UQ_RPM UQ_RATE_FILE REACT_API_KEY PROBE_API_KEY
mkdir -p $OUT
export REACT_MODEL=qwen REACT_TOKENIZER=$SNAP REACT_BASE_URL=http://localhost:$PORT/v1
export PROBE_MODEL=qwen PROBE_TOKENIZER=$SNAP PROBE_BASE_URL=http://localhost:$PORT/v1

ALF_TASKS=$RD/result/ctxrule/uqfb_tasks_alfworld.txt
HOT_TASKS=$RD/result/ctxrule/uqfb_tasks_hotpot.txt
for f in $ALF_TASKS $HOT_TASKS; do
  [ -s "$f" ] || { echo "MISSING_TASKS $f"; exit 1; }
done
echo "=== [uqfb] START $(date) | alfworld $(wc -l < $ALF_TASKS) eps | hotpot $(wc -l < $HOT_TASKS) eps ==="

pick_gpu() {
  nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits 2>/dev/null |
  while IFS=', ' read -r idx free; do
    case "$free" in ''|*[!0-9]*) continue ;; esac
    case " $EXCLUDE_GPUS " in *" $idx "*) continue ;; esac
    [ "$free" -ge "$NEED_MIB" ] && { echo "$idx"; break; }
  done
}
deadline=$(( $(date +%s) + MAX_WAIT_H * 3600 )); last_report=0
wait_for_gpu() {
  while :; do
    GPU=$(pick_gpu)
    if [ -n "$GPU" ]; then
      echo "[uqfb] candidate GPU$GPU — settling 20s"; sleep 20
      re=$(nvidia-smi --id=$GPU --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null)
      case "$re" in ''|*[!0-9]*) re=0 ;; esac
      [ "$re" -ge "$NEED_MIB" ] && { echo "[uqfb] TAKING GPU$GPU (${re}MiB)"; return 0; }
      echo "[uqfb] GPU$GPU taken during settle — waiting"; GPU=
    fi
    [ "$(date +%s)" -ge "$deadline" ] && { echo "[uqfb] GAVE_UP"; return 1; }
    now=$(date +%s)
    if [ $(( now - last_report )) -ge 1800 ]; then
      echo "[uqfb] $(date +%H:%M) waiting | free: $(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | tr '\n' ' ')"
      last_report=$now
    fi
    sleep $POLL
  done
}

SRV=; FREED=0
free_gpu() {
  [ "$FREED" = 1 ] && return 0
  FREED=1
  SPGID=$(ps -o pgid= -p $SRV 2>/dev/null | tr -d ' ')
  if [ -n "$SPGID" ] && [ "$SPGID" != "$(ps -o pgid= -p $$ | tr -d ' ')" ]; then kill -9 -$SPGID 2>/dev/null; fi
  pkill -9 -f -- "--port $PORT" 2>/dev/null
  sleep 8
  echo "=== [uqfb] GPU$GPU freed $(date) ==="
}
trap free_gpu EXIT INT TERM

attempt=0
while :; do
  attempt=$(( attempt + 1 ))
  [ "$attempt" -gt "$MAX_ATTEMPTS" ] && { echo "[uqfb] GAVE_UP after $MAX_ATTEMPTS serve attempts"; exit 3; }
  wait_for_gpu || exit 2
  : > /tmp/uqfb_serve.log
  CUDA_VISIBLE_DEVICES=$GPU setsid nohup $V serve "$SNAP" --served-model-name qwen \
    --tensor-parallel-size 1 --max-model-len 16384 \
    --gpu-memory-utilization 0.90 --max-num-seqs 64 \
    --port $PORT >> /tmp/uqfb_serve.log 2>&1 &
  SRV=$!
  ready=0
  for i in $(seq 1 180); do
    curl -sS http://localhost:$PORT/v1/models >/dev/null 2>&1 && { ready=1; break; }
    grep -qiE "Engine core initialization failed|out of memory|ValueError" /tmp/uqfb_serve.log 2>/dev/null && break
    kill -0 $SRV 2>/dev/null || break
    sleep 10
  done
  if [ "$ready" = 1 ]; then
    # CANARY: a served model can load perfectly and still emit NaN logits, which surfaces as
    # HTTP 400 "Out of range float values are not JSON compliant: nan" on every request. A short
    # single-request check is NOT enough — GPU1 passed exactly that and then failed every real
    # call — so the canary uses the real probe path with LONG prompts and CONCURRENCY.
    if PROBE_BASE_URL=http://localhost:$PORT/v1 PROBE_MODEL=qwen PROBE_TOKENIZER=$SNAP \
         $PY -u src/uqfb_canary.py; then
      echo "[uqfb] SERVER_READY + CANARY OK on GPU$GPU $(date)"
      break
    fi
    # A vLLM instance of this model is NONDETERMINISTICALLY born broken: it loads cleanly,
    # captures CUDA graphs, reports healthy, and then emits NaN logprobs for every request
    # (server-side ValueError at JSON serialization). Verified same-GPU: one instance healthy,
    # the next sick, identical flags. NOT the GPU, NOT the compile cache, NOT the code — so
    # just restart the server and draw again, on the same card.
    echo "[uqfb] CANARY FAILED on GPU$GPU (instance born broken) — restarting the server"
    FREED=0; free_gpu; FREED=0; sleep 20
    continue
  fi
  echo "[uqfb] serve attempt $attempt FAILED"; grep -m2 -E "ValueError|out of memory" /tmp/uqfb_serve.log | cut -c1-160
  FREED=0; free_gpu; FREED=0; sleep 60
done

# ---- 1. calibrate hotpot/c5 (the one threshold never measured before)
echo "=== [uqfb] calibrating hotpot/c5 threshold $(date) ==="
$PY -u src/uq_feedback_calibrate.py --uq runs/hotpot_500/uq_hotpot_entangled.jsonl \
  --judge runs/hotpot_500/judge_hotpot_entangled.jsonl --domain hotpot --arm c5 --n 150 \
  --out $OUT/calib_hotpot_c5.jsonl > $OUT/calib_hotpot_c5.log 2>&1
THR_HOT_C5=$(grep -oP 'UQFB_THRESH_HOTPOT_C5=\K[0-9.]+' $OUT/calib_hotpot_c5.log | tail -1)
tail -5 $OUT/calib_hotpot_c5.log
if [ -n "$THR_HOT_C5" ]; then
  export UQFB_THRESH_HOTPOT_C5=$THR_HOT_C5
  echo "[uqfb] hotpot/c5 threshold = $THR_HOT_C5"
else
  echo "[uqfb] WARNING: calibration failed, using the built-in provisional hotpot/c5 threshold"
fi

# ---- 1b. SMOKE: one episode per domain on the c5 arm (the most complex path). A plumbing bug
#          should cost 2 minutes here, not an hour of full runs.
echo "=== [uqfb] SMOKE $(date) ==="
head -1 $ALF_TASKS > /tmp/uqfb_smoke_alf.txt
head -1 $HOT_TASKS > /tmp/uqfb_smoke_hot.txt
rm -f $OUT/smoke_alf.jsonl $OUT/smoke_hot.jsonl
UQFB_ARM=c5 UQFB_TASKS=/tmp/uqfb_smoke_alf.txt UQFB_LOG=$OUT/smoke_alf.jsonl \
  UQFB_SEED_BASE=2000 REACT_SPLIT=eval_in_distribution REACT_MAX_STEPS=3 \
  $PY -u src/uq_feedback_alfworld.py > $OUT/smoke_alf.log 2>&1
UQFB_ARM=c5 UQFB_TASKS=/tmp/uqfb_smoke_hot.txt UQFB_LOG=$OUT/smoke_hot.jsonl \
  UQFB_SEED_BASE=2000 REACT_MAX_STEPS=2 REACT_SPLIT=dev \
  $PY -u src/uq_feedback_hotpot.py > $OUT/smoke_hot.log 2>&1
alf_u=$(grep -c '"U_feedback": [0-9]' $OUT/smoke_alf.jsonl 2>/dev/null || echo 0)
hot_u=$(grep -c '"U_feedback": [0-9]' $OUT/smoke_hot.jsonl 2>/dev/null || echo 0)
echo "[uqfb] smoke: alfworld steps with a measured U = $alf_u | hotpot = $hot_u"
if [ "$alf_u" -lt 1 ] || [ "$hot_u" -lt 1 ]; then
  echo "SMOKE_FAILED — no uncertainty was measured; aborting before the full run"
  echo "--- alfworld ---"; tail -20 $OUT/smoke_alf.log
  echo "--- hotpot ---";   tail -20 $OUT/smoke_hot.log
  exit 4
fi
grep -m1 -o '\[uncertainty [0-9.]*[^]]*\]' $OUT/smoke_alf.jsonl && echo "[uqfb] annotation format OK"

# ---- 2. ALFWorld, 3 arms x NWORK shards, all concurrent
echo "=== [uqfb] ALFWorld $(date) ==="
pids=()
for arm in control prod c5; do
  rm -f $OUT/uqfb_alfworld_${arm}.w*.jsonl
  for w in $(seq 0 $((NWORK-1))); do
    UQFB_ARM=$arm UQFB_TASKS=$ALF_TASKS UQFB_LOG=$OUT/uqfb_alfworld_${arm}.w${w}.jsonl \
    UQFB_NUM_WORKERS=$NWORK UQFB_WORKER_ID=$w UQFB_SEED_BASE=2000 \
    REACT_SPLIT=eval_in_distribution REACT_MAX_STEPS=50 \
      $PY -u src/uq_feedback_alfworld.py > $OUT/alfworld_${arm}_w${w}.log 2>&1 &
    pids+=($!)
  done
done
wait "${pids[@]}"
for arm in control prod c5; do
  cat $OUT/uqfb_alfworld_${arm}.w*.jsonl > $OUT/uqfb_alfworld_${arm}.jsonl 2>/dev/null
  n=$(grep -c '"kind": "episode"' $OUT/uqfb_alfworld_${arm}.jsonl 2>/dev/null || echo 0)
  s=$(grep '"kind": "episode"' $OUT/uqfb_alfworld_${arm}.jsonl 2>/dev/null | grep -c '"success": true' || true)
  echo "ALFWORLD[$arm] recovered $s/$n"
done

# ---- 3. HotpotQA, 3 arms concurrent (live Wikipedia; one process per arm)
echo "=== [uqfb] HotpotQA $(date) ==="
pids=()
for arm in control prod c5; do
  rm -f $OUT/uqfb_hotpot_${arm}.jsonl
  UQFB_ARM=$arm UQFB_TASKS=$HOT_TASKS UQFB_LOG=$OUT/uqfb_hotpot_${arm}.jsonl \
  UQFB_SEED_BASE=2000 REACT_MAX_STEPS=7 REACT_SPLIT=dev \
    $PY -u src/uq_feedback_hotpot.py > $OUT/hotpot_${arm}.log 2>&1 &
  pids+=($!)
done
wait "${pids[@]}"
for arm in control prod c5; do
  echo "HOTPOT[$arm] $(grep -h '^FINAL' $OUT/hotpot_${arm}.log | tail -1)"
done

free_gpu; trap - EXIT INT TERM
echo "UQFB_DONE $(date)"
grep -hE "^ALFWORLD\[|^HOTPOT\[" /tmp/uqfb_gate.out 2>/dev/null | tail -10
