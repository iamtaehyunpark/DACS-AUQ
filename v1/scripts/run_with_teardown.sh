#!/usr/bin/env bash
# Serve one or more vLLM backends, wait for readiness, run a driver command,
# then tear the server(s) down unconditionally (trap on EXIT) so GPUs are
# freed even if the controlling ssh/lg connection drops mid-run. Meant to be
# launched via `lg run -d --` so the whole lifecycle runs server-side under
# systemd --user, independent of the client connection.
#
# Usage:
#   run_with_teardown.sh <serve_script:port> [serve_script2:port2] -- <command...>
# Example:
#   run_with_teardown.sh serve_agent.sh:8000 -- \
#     env ALFWORLD_DATA=/home/user/.cache/alfworld PYTHONPATH=<DACS> \
#     /opt/anaconda3/envs/Jagent/bin/python -m src.run --config configs/e0_gen.yaml \
#     --stage generate --condition entangled_auq
set -uo pipefail
DACS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DACS_DIR"

SERVE_SPECS=()
while [[ $# -gt 0 && "$1" != "--" ]]; do
  SERVE_SPECS+=("$1")
  shift
done
if [[ "${1:-}" == "--" ]]; then shift; fi

PIDS=()
cleanup() {
  local rc=$?
  echo "[teardown] cleaning up ${#PIDS[@]} server(s): ${PIDS[*]:-none} (triggering exit code $rc)"
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null
  done
  for pid in "${PIDS[@]:-}"; do
    wait "$pid" 2>/dev/null
  done
  echo "[teardown] done"
}
trap cleanup EXIT

for spec in "${SERVE_SPECS[@]:-}"; do
  [[ -z "$spec" ]] && continue
  script="${spec%%:*}"
  port="${spec##*:}"
  NCCL_NET_PLUGIN=none NCCL_IB_DISABLE=1 bash "$DACS_DIR/scripts/$script" &
  pid=$!
  PIDS+=("$pid")
  echo "[setup] launched $script (pid $pid), waiting on port $port"
  tries=0
  # Probe a REAL completion, not just /v1/models: vLLM serves /v1/models (and even
  # /tokenize with 0 tokens) before the engine can actually generate, so a models-only
  # check races ahead of readiness and the first request 404s ("model does not exist").
  until curl -s -m 8 "http://localhost:$port/v1/completions" \
        -H 'Content-Type: application/json' \
        -d '{"model":"agent","prompt":"ready","max_tokens":1}' 2>/dev/null | grep -q '"text"'; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "[setup] $script (pid $pid) died before becoming ready"
      exit 1
    fi
    tries=$((tries + 1))
    if [[ $tries -gt 120 ]]; then
      echo "[setup] $script did not become ready after 20 minutes"
      exit 1
    fi
    sleep 10
  done
  echo "[setup] $script ready on port $port"
done

echo "[run] $*"
"$@"
rc=$?
echo "[run] exited with code $rc"
exit $rc
