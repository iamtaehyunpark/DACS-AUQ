# Handover — S4 / GATE-4 scoring throughput

**2026-08-07 · Facts only. No proposed remedies.**
Repo: `/data5/kje/MULTIAGENT/DACS-AUQ` (server) · branch `s0-execution-harness`

## 1. What we want to run

**S4 hindsight-ceiling pass** (`docs/specs/S4_SPEC.md`). Two capable judges,
Llama-3.3-70B-Instruct and Qwen3.6-35B-A3B, each scoring all 11 `in_matrix` arms —
**44,573 steps per judge**. Each step is one request: a hindsight prompt, `max_tokens=1`,
`logprobs=True, top_logprobs=20`; P(True) is read off the first token.
Driver `analysis/s4_hindsight.py`, runner `scripts/run_s4_hindsight.sh`.

- Qwen judge: **complete** (44,573/44,573).
- Llama judge: **~11,700/44,573 done**, still running.

**GATE-4 Part A scoring** (`docs/specs/GATE4_SPEC_A34.md`). Both capable judges must
P(True)-score five forecast targets never previously cross-probed — `Qwen3.5-4B/9B/27B`
on alfworld, `Qwen3.5-4B/9B` on hotpotqa — **17,492 steps per judge**. Online-length
prompts. Driver `src/run_probes.py` via `scripts/run_crossprobe_matrix.sh`.

- Qwen3.6 assessor: **complete** (all 5 cells present under
  `result/pivot/crossprobe/<ds>/<target>/ptrue.Qwen3.6-35B-A3B.response.jsonl`).
- Llama assessor: **running** on GPUs 2,3, port 8094.

## 2. Measured throughput

| pass | judge | rate | prefill | notes |
|---|---|---|---|---|
| S4 hindsight | Qwen3.6-35B-A3B | 2.6 steps/s | ~5,700 tok/s | TP=1, one GPU |
| S4 hindsight | Llama-3.3-70B | **0.21 steps/s** | ~1,760 tok/s | TP=2, GPUs 0,1 |

Mean hindsight prompt **6,957 tokens**, max observed 35,448.
At 1,760 tok/s a 7k prompt takes ~4 s → ~0.25 req/s, consistent with the 0.21 observed.
2×A100 bf16 peak ≈ 624 TFLOP/s; 70B at 1,760 tok/s ≈ 246 TFLOP/s ⇒ **~39% MFU**.

Remaining Llama S4 work at the current rate: ~33,000 steps ≈ **26–37 h wall,
~55–75 A100-hours**. Author-approved budget for the whole pass was 17.1 A100-hours;
~45 A100-hours were already spent before the current run.

## 3. Server-side observations (S4 Llama, port 8072)

vLLM engine log lines, verbatim pattern:

```
Avg prompt throughput: 1760.2 tokens/s, Avg generation throughput: 0.4 tokens/s,
Running: 2 reqs, Waiting: 21 reqs, GPU KV cache usage: 9.1%,
Prefix cache hit rate: 11.1%
```

Facts in that line:
- **Running never exceeds 2**, Waiting sits at 21–22, with 24–32 client requests
  in flight. `--max-num-seqs` is 64.
- **GPU KV cache usage 5.8–12.9%.**
- **Prefix cache hit rate 11–15%.**
- Raising `--max-num-batched-tokens` from the default to 65536 changed none of the
  above; prompt throughput stayed ~1,760 tok/s.

## 4. Prompt structure (relevant to the cache numbers)

`analysis/s4_hindsight.py::assemble()` emits, in this order:

1. the banked per-step online prompt — **varies per step**;
2. `FULL TRAJECTORY (including everything after this step): …` — **identical for every
   step in the episode**, ~6,000 tokens;
3. `EPISODE OUTCOME: …` — identical for the episode;
4. the Yes/No question — constant.

Episodes average ~34 steps (e.g. alfworld/Llama arm: 4,765 steps / 140 episodes).

## 5. Client structure

`s4_hindsight.py` issues requests through a `ThreadPoolExecutor`, `--conc` default 24
(currently launched with 24–32). Before 2026-08-07 it was a serial loop; the server
reported `Running: 1 reqs` then, and the change moved the observed rate from 0.20 to
0.21 steps/s.

A `/tokenize` round trip was previously made for every step; it is now made only when
`len(text)//2 >= ctx-64`.

## 6. Environment inconsistency

| script | server | client |
|---|---|---|
| `scripts/run_crossprobe_matrix.sh` (banked matrix + GATE-4 Part A) | `/opt/anaconda3/envs/yllm/bin/vllm` | `/opt/anaconda3/envs/Jagent/bin/python` |
| `scripts/run_s4_hindsight.sh` (S4) | `/opt/anaconda3/envs/yllm/bin/vllm` | `/opt/anaconda3/envs/yllm/bin/python` |

Every banked cross-probe cell in the matrix was produced with the Jagent client.
S4 uses the yllm client for both. The two passes therefore run different client envs.

## 7. Serving parameters in use

| | S4 (`run_s4_hindsight.sh`) | cross-probe (`run_crossprobe_matrix.sh`) |
|---|---|---|
| `--max-model-len` | 32768 | 16384 |
| `--gpu-memory-utilization` | 0.95 | 0.90 (Llama/Qwen), 0.30 (small) |
| `--max-num-seqs` | 64 Llama / 128 Qwen | 64 |
| `--max-num-batched-tokens` | 65536 | unset (default) |
| client concurrency | 24–32 threads | 8 shards × 8 |

`scripts/run_crossprobe_matrix.sh:37-41` carries this note from the original author:
> Client-side concurrency is the real throughput limit, not the server: at SHARDS=8 the
> engine reported "Running: 4-5 reqs" against a 64-seq capacity, i.e. coasting.

Shard count is baked into `.done` marker filenames; changing it orphans existing
markers and re-probes finished cells.

## 8. GPU topology

GPUs 0 and 1 are interconnected. GPU 1 and GPU 2 are not. Llama-70B runs TP=2 and was
initially placed on 1,2; moving it to 0,1 changed the observed rate from 0.154 to
~0.20 steps/s.

Current occupancy: GPUs 0,1 = S4 Llama (port 8072). GPUs 2,3 = GATE-4 Llama scoring
(port 8094). GPU 4 idle. Other users are active on this host (VS Code servers,
Jupyter kernels under the `vad` env); none currently hold GPU memory.

## 9. Operational notes

- Both drivers are **resumable**: completed records are read back and skipped, so a
  killed run resumes rather than restarting.
- `pkill -f "vllm serve"` does **not** match the `VLLM::EngineCore` child. It survives
  its parent holding the full GPU allocation, which blocks the next server from
  starting. Killing by `nvidia-smi -i <gpu> --query-compute-apps=pid` does match it.
- S4 output: `result/hindsight/<dataset>/<model>/hindsight.<judge>.jsonl`, one record
  per step with `U`, `first_token_top`, `route`, `truncated`, `n_elided`,
  `prompt_tokens`.
- Route coverage for the completed Qwen judge, in-matrix arms only: **44,573/44,573
  route=main**, 0 truncated, 0 failed, 0 deferred.
