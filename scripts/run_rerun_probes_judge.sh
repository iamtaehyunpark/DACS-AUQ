#!/usr/bin/env bash
set -euo pipefail

RD=/data5/kje/MULTIAGENT/DACS-AUQ/react_validation
OUT=$RD/result/rerun
PY=/opt/anaconda3/envs/Jagent/bin/python
VLLM=/opt/anaconda3/envs/yllm/bin/vllm
QWEN_TOKENIZER=Qwen/Qwen3.6-35B-A3B
LLAMA_TOKENIZER=/data3/hg_weight/hg_weight/models--meta-llama--Llama-3.3-70B-Instruct/snapshots/6f6073b423013f6a7d4d9f39144961bfbfbc386b
NW=8
SERVER_PID=

cd "$RD"
mkdir -p "$OUT"
export HF_HOME=/data5/user/hf_cache
export HF_HUB_OFFLINE=1

log() {
  printf '[rerun-p23] %s %s\n' "$(date -Is)" "$*"
}

stop_server() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill -TERM -- "-$SERVER_PID" 2>/dev/null || true
    for _ in $(seq 1 30); do
      kill -0 "$SERVER_PID" 2>/dev/null || break
      sleep 1
    done
    kill -KILL -- "-$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  SERVER_PID=
}
trap stop_server EXIT INT TERM

wait_api() {
  local port=$1
  local logfile=$2
  for _ in $(seq 1 180); do
    if curl -fsS "http://localhost:${port}/v1/models" >/dev/null 2>&1; then
      return 0
    fi
    if grep -qiE 'Engine core initialization failed|out of memory|ValueError|Traceback' "$logfile" 2>/dev/null; then
      log "server startup failed; see $logfile"
      return 1
    fi
    sleep 10
  done
  log "server startup timed out; see $logfile"
  return 1
}

probe_pass() {
  local tag=$1
  local model=$2
  local tokenizer=$3
  local input=$4
  local output=$5
  local stages=$6
  local kinds=$7
  local base=${output%.jsonl}
  local pids=()
  local rc=0

  if [[ -e "$output" ]]; then
    log "refusing to overwrite existing $output"
    return 1
  fi
  for w in $(seq 0 $((NW - 1))); do
    if [[ -e "${base}.w${w}.jsonl" ]]; then
      log "refusing to append to existing ${base}.w${w}.jsonl"
      return 1
    fi
  done

  log "starting $tag with $NW workers"
  for w in $(seq 0 $((NW - 1))); do
    PROBE_INPUT="$input" \
    PROBE_OUTPUT="${base}.w${w}.jsonl" \
    PROBE_NUM_WORKERS="$NW" \
    PROBE_WORKER_ID="$w" \
    PROBE_BASE_URL=http://localhost:8000/v1 \
    PROBE_MODEL="$model" \
    PROBE_TOKENIZER="$tokenizer" \
    PROBE_KINDS="$kinds" \
    PROBE_STAGES="$stages" \
    PROBE_RESPONSE_KINDS= \
    PROBE_TEMPERATURE=0 \
    PROBE_TOP_P=1.0 \
    PROBE_PRESENCE_PENALTY=0 \
    PROBE_REPETITION_PENALTY=1.0 \
      "$PY" -u src/run_probes.py > "${base}_w${w}.log" 2>&1 &
    pids+=("$!")
  done
  for pid in "${pids[@]}"; do
    wait "$pid" || rc=1
  done
  if [[ "$rc" -ne 0 ]]; then
    log "$tag failed; preserving worker logs and partial JSONL files"
    return 1
  fi
  for w in $(seq 0 $((NW - 1))); do
    cat "${base}.w${w}.jsonl"
  done > "$output"
  log "finished $tag records=$(wc -l < "$output")"
}

judge_one() {
  local name=$1
  local input=$2
  local output=$3
  source "$HOME/.config/azure_judge.env"
  log "starting judge $name"
  JUDGE_INPUT="$input" JUDGE_OUTPUT="$output" JUDGE_WORKERS=8 \
    "$PY" -u src/judge_e0.py > "${output%.jsonl}.log" 2>&1
  log "finished judge $name records=$(wc -l < "$output")"
}

QWEN_UQ=$OUT/uq_decoupled_rerun_qwen.jsonl
LLAMA_UQ=$OUT/uq_decoupled_rerun_llama.jsonl
for input in "$QWEN_UQ" "$LLAMA_UQ"; do
  [[ -s "$input" ]] || { log "missing input $input"; exit 1; }
done

# Judges use external APIs and can safely overlap the local probe acquisition.
judge_one qwen "$QWEN_UQ" "$OUT/judge_decoupled_rerun_qwen.jsonl" &
JUDGE_QWEN_PID=$!
judge_one llama "$LLAMA_UQ" "$OUT/judge_decoupled_rerun_llama.jsonl" &
JUDGE_LLAMA_PID=$!

log "starting Qwen on GPU 0"
setsid env CUDA_VISIBLE_DEVICES=0 \
  "$VLLM" serve Qwen/Qwen3.6-35B-A3B \
  --served-model-name qwen \
  --tensor-parallel-size 1 \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.95 \
  --max-num-seqs 128 \
  --port 8000 > "$OUT/serve_qwen.log" 2>&1 &
SERVER_PID=$!
wait_api 8000 "$OUT/serve_qwen.log"

probe_pass qwen-stage qwen "$QWEN_TOKENIZER" "$QWEN_UQ" \
  "$OUT/probes_decoupled_rerun_qwen.jsonl" \
  thought,action ptrue,sep_verbalized,posthoc_numeric,targeted
probe_pass qwen-response-ptrue qwen "$QWEN_TOKENIZER" "$QWEN_UQ" \
  "$OUT/probes_decoupled_rerun_qwen.aggtrue_ptrue.jsonl" \
  response ptrue
stop_server
log "Qwen probes complete; GPU 0 freed"

# The frozen Llama-3.3-70B checkpoint needs two A100s. Preserve unrelated GPU-1
# work: wait until both GPUs are free instead of killing another user's process.
while true; do
  used0=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 0 | tr -d ' ')
  used1=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 1 | tr -d ' ')
  if [[ "$used0" -lt 2000 && "$used1" -lt 2000 ]]; then
    break
  fi
  log "waiting for Llama GPUs 0,1 (used MiB: $used0,$used1)"
  sleep 60
done

log "starting Llama-3.3-70B on GPUs 0,1"
setsid env CUDA_VISIBLE_DEVICES=0,1 \
  NCCL_NET_PLUGIN=none NCCL_IB_DISABLE=1 NCCL_SOCKET_IFNAME=lo VLLM_HOST_IP=127.0.0.1 \
  "$VLLM" serve "$LLAMA_TOKENIZER" \
  --served-model-name llama70b \
  --tensor-parallel-size 2 \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.95 \
  --max-num-seqs 48 \
  --port 8000 > "$OUT/serve_llama70b.log" 2>&1 &
SERVER_PID=$!
wait_api 8000 "$OUT/serve_llama70b.log"

probe_pass llama-stage llama70b "$LLAMA_TOKENIZER" "$LLAMA_UQ" \
  "$OUT/probes_decoupled_rerun_llama.jsonl" \
  thought,action ptrue,sep_verbalized,posthoc_numeric,targeted
probe_pass llama-response-ptrue llama70b "$LLAMA_TOKENIZER" "$LLAMA_UQ" \
  "$OUT/probes_decoupled_rerun_llama.aggtrue_ptrue.jsonl" \
  response ptrue
stop_server

wait "$JUDGE_QWEN_PID"
wait "$JUDGE_LLAMA_PID"
log "ALL_RERUN_PROBES_JUDGES_DONE"
