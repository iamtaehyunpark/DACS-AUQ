import json, glob, statistics, sys

d = sys.argv[1] if len(sys.argv) > 1 else "result/deepseek"
lat, ctok, aligned, samples = [], [], [], []
for f in sorted(glob.glob(d + "/uq_decoupled_ds.w*.jsonl")):
    for l in open(f):
        try:
            r = json.loads(l)
        except Exception:
            continue
        if r.get("kind") != "call":
            continue
        gl = r.get("gen_logprobs") or []
        joined = "".join(t["token"] for t in gl)
        raw = r.get("completion_raw") or ""
        lat.append((r.get("latency_ms") or 0) / 1000.0)
        ctok.append(r.get("completion_tokens") or 0)
        aligned.append(joined.strip() == raw.strip())
        if len(samples) < 2:
            samples.append(joined[:100])

n = len(lat)
print("  calls=%d" % n)
if n:
    print("  latency: mean %.1fs  median %.1fs  max %.1fs" % (
        statistics.mean(lat), statistics.median(lat), max(lat)))
    print("  completion_tokens: mean %.0f  max %d" % (statistics.mean(ctok), max(ctok)))
    print("  logprobs aligned with content: %d/%d (%.0f%%)" % (
        sum(aligned), n, 100.0 * sum(aligned) / n))
    for s in samples:
        print("  sample logprob-token start: %r" % s)
