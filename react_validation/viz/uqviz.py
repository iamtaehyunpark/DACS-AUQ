import json, math, sys, html
from collections import defaultdict

def H(top):
    ps = [math.exp(a["logprob"]) for a in top]
    return -sum(p * math.log(p) for p in ps if p > 0)

def metrics(gen, span):
    if not span:
        return None
    toks = gen[span[0]:span[1]]
    if not toks:
        return None
    Hs = [H(t["top"]) for t in toks]
    own = [t["logprob"] for t in toks]
    n = len(toks); nll = -sum(own)
    return {"n": n, "mte": sum(Hs) / n, "maxte": max(Hs), "ppl": math.exp(nll / n),
            "nll": nll, "toks": toks, "Hs": Hs}

def col(h, hmax=4.0):
    f = min(max(h, 0) / hmax, 1.0)
    return "rgb(%d,%d,%d)" % (int(40 + 215 * f), int(190 * (1 - f) + 30), int(120 * (1 - f) + 30))

def heat(m):
    if not m:
        return "<i>(none)</i>"
    out = []
    for t, h in zip(m["toks"], m["Hs"]):
        tk = html.escape(t["token"]).replace(" ", "&nbsp;").replace("\n", "↵")
        out.append('<span class="tk" style="background:%s" title="H=%.2f lp=%.2f">%s</span>'
                   % (col(h), h, t["logprob"], tk))
    return "".join(out)

path, label, out = sys.argv[1], sys.argv[2], sys.argv[3]
ep_idx = int(sys.argv[4]) if len(sys.argv) > 4 else 0
recs = [json.loads(l) for l in open(path)]
# segment into episodes (an "episode" record closes one); step_idx repeats per episode.
episodes, cur = [], []
for r in recs:
    cur.append(r)
    if r["kind"] == "episode":
        episodes.append(cur); cur = []
if cur:
    episodes.append(cur)
n_ep = len(episodes)
buf = episodes[min(ep_idx, n_ep - 1)] if episodes else []
calls = [r for r in buf if r["kind"] == "call"]
steps = {r["step_idx"]: r for r in buf if r["kind"] == "step"}
ep = next((r for r in buf if r["kind"] == "episode"), {})
cfg = calls[0]["config"] if calls else {}

# optional Phase-2 probe log: index this episode's probes by (step, probe_kind, stage)
probe_path = sys.argv[5] if len(sys.argv) > 5 else None
pv = {}
if probe_path:
    tid = ep.get("task_id")
    for l in open(probe_path):
        r = json.loads(l)
        if r.get("kind") == "probe" and r.get("task_id") == tid and r.get("parse_ok"):
            # store U = normalized UNCERTAINTY (1 = max uncertain); all metrics point the same way
            pv[(r["step_idx"], r["probe_kind"], r["stage"])] = r.get("U")

def pval(si, kind, stage):
    v = pv.get((si, kind, stage))
    return "%.2f" % v if isinstance(v, (int, float)) else "-"
by = defaultdict(dict)
for c in calls:
    by[c["step_idx"]][c["call_kind"]] = c

def stage_metrics(cc):
    tm = am = None
    if "thought" in cc:
        tm = metrics(cc["thought"]["gen_logprobs"], cc["thought"]["spans"]["thought"])
    if "action" in cc:
        am = metrics(cc["action"]["gen_logprobs"], cc["action"]["spans"]["action"])
    if "joint" in cc:
        j = cc["joint"]
        tm = metrics(j["gen_logprobs"], j["spans"]["thought"])
        am = metrics(j["gen_logprobs"], j["spans"]["action"])
    return tm, am

P = []
P.append("<style>")
P.append(":root{--bg:#fbfcfd;--panel:#ffffff;--ink:#19212b;--muted:#5b6672;--line:#e2e7ee;"
         "--accent:#3b5bdb;--ok:#2f9e57;--bad:#d1443e;--head:#f2f5f9}")
P.append("@media(prefers-color-scheme:dark){:root{--bg:#0e1116;--panel:#161b22;--ink:#d7dde5;"
         "--muted:#8b95a3;--line:#263040;--accent:#8da0ff;--ok:#48c17e;--bad:#f2685f;--head:#1b222c}}")
P.append(':root[data-theme="light"]{--bg:#fbfcfd;--panel:#fff;--ink:#19212b;--muted:#5b6672;--line:#e2e7ee;--accent:#3b5bdb;--ok:#2f9e57;--bad:#d1443e;--head:#f2f5f9}')
P.append(':root[data-theme="dark"]{--bg:#0e1116;--panel:#161b22;--ink:#d7dde5;--muted:#8b95a3;--line:#263040;--accent:#8da0ff;--ok:#48c17e;--bad:#f2685f;--head:#1b222c}')
P.append("body{font:14px/1.55 ui-sans-serif,system-ui,-apple-system,sans-serif;margin:0;"
         "padding:32px 28px;max-width:1120px;background:var(--bg);color:var(--ink)}")
P.append("h1{font-size:21px;font-weight:650;letter-spacing:-.01em;margin:0 0 4px;text-wrap:balance}")
P.append(".sub{color:var(--muted);font-size:12.5px;margin-bottom:22px;line-height:1.7}")
P.append("code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em;color:var(--accent)}")
P.append("table{border-collapse:collapse;width:100%;font-size:12.5px;margin:8px 0;"
         "font-variant-numeric:tabular-nums}")
P.append("th{color:var(--muted);font-weight:600;font-size:11px;letter-spacing:.03em;"
         "text-transform:uppercase;background:var(--head);position:sticky;top:0}")
P.append("th,td{border-bottom:1px solid var(--line);padding:6px 9px;text-align:right}")
P.append("th:nth-child(2),td:nth-child(2){text-align:left}")
P.append("td.a{text-align:left;font-family:ui-monospace,monospace;font-size:11.5px;color:var(--muted)}")
P.append("tr:hover td{background:color-mix(in srgb,var(--accent) 6%,transparent)}")
P.append(".bad{color:var(--bad);font-weight:600}.ok{color:var(--ok)}")
P.append(".tk{padding:1px 0;border-radius:2px;color:#0b0d10;"
         "font-family:ui-monospace,monospace;font-size:12px}")
P.append(".card{border:1px solid var(--line);border-radius:10px;padding:13px 15px;margin:14px 0;"
         "background:var(--panel)}")
P.append(".lbl{font-weight:600;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;"
         "color:var(--muted);margin-bottom:7px}")
P.append(".legend{display:inline-block;height:11px;width:150px;border-radius:2px;vertical-align:middle;"
         "background:linear-gradient(90deg,rgb(40,190,30),rgb(230,170,20),rgb(255,40,40))}")
P.append("</style>")
P.append("<h1>UQ inspection — %s</h1>" % html.escape(label))
P.append('<div class="sub">episode %d of %d · <code>%s</code> · %s (%s, %s steps) · sampling T=%s top_p=%s top_k=%s pres=%s rep=%s · per-token entropy over top-20 logprobs, color <span class="legend"></span> low→high (0→%s nats)</div>'
         % (min(ep_idx, n_ep - 1) + 1, n_ep,
            html.escape((ep.get("task_id", "") or "").split("/")[0]),
            "success" if ep.get("success") else "fail", ep.get("terminal_reason", "?"),
            ep.get("n_steps", "?"),
            cfg.get("temperature"), cfg.get("top_p"), cfg.get("top_k"),
            cfg.get("presence_penalty"), cfg.get("repetition_penalty"), 4.0))

def f2(m, k):
    return "%.2f" % m[k] if m else "-"
has_p = bool(pv)
S = sorted(by)
sd = {si: stage_metrics(by[si]) for si in S}          # (thought_metrics, action_metrics) per step

def mte(si, stage):
    m = sd[si][0] if stage == "t" else sd[si][1]
    return m["mte"] if m else None

def unc(si, kind, stage):        # normalized uncertainty U (↑ = uncertain)
    v = pv.get((si, kind, stage))
    return v if isinstance(v, (int, float)) else None

def confval(si):  # env-side failure/loop markers to shade the x-axis
    st = steps.get(si, {})
    return (not st.get("in_admissible", True)) or st.get("loop_flag", False)

def svg_chart(series, ymin, ymax, title, ann=""):
    W, H, ml, mr, mt, mb = 1000, 210, 46, 172, 26, 28
    iw, ih = W - ml - mr, H - mt - mb
    n = max(len(S) - 1, 1)
    X = lambda i: ml + iw * (i / n)
    Y = lambda v: mt + ih * (1 - (v - ymin) / (ymax - ymin if ymax > ymin else 1))
    o = ['<svg viewBox="0 0 %d %d" width="100%%" style="max-width:%dpx;font:11px ui-sans-serif;display:block;margin:6px 0">' % (W, H, W)]
    o.append('<text x="%d" y="13" style="font-weight:650;fill:var(--ink)">%s</text>' % (ml, title))
    if ann:
        o.append('<text x="%d" y="13" text-anchor="end" style="fill:var(--muted)">%s</text>' % (ml + iw, ann))
    # shade failed/loop steps
    for i, si in enumerate(S):
        if confval(si):
            o.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="var(--bad)" opacity="0.07"/>' % (X(i) - iw / n / 2, mt, iw / n, ih))
    for t in range(5):                                   # y grid + labels
        v = ymin + (ymax - ymin) * t / 4; y = Y(v)
        o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="var(--line)"/>' % (ml, y, ml + iw, y))
        o.append('<text x="%d" y="%.1f" text-anchor="end" style="fill:var(--muted)">%.2f</text>' % (ml - 6, y + 3, v))
    for i, si in enumerate(S):                           # x labels
        if i % 5 == 0 or i == len(S) - 1:
            o.append('<text x="%.1f" y="%d" text-anchor="middle" style="fill:var(--muted)">%d</text>' % (X(i), H - 9, si))
    for j, (lab, col, ys) in enumerate(series):
        pts = " ".join("%.1f,%.1f" % (X(i), Y(v)) for i, v in enumerate(ys) if v is not None)
        if pts:
            o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round"/>' % (pts, col))
            for i, v in enumerate(ys):
                if v is not None:
                    o.append('<circle cx="%.1f" cy="%.1f" r="1.7" fill="%s"/>' % (X(i), Y(v), col))
        ly = mt + 17 * j + 6
        o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="3"/>' % (ml + iw + 12, ly, ml + iw + 30, ly, col))
        o.append('<text x="%d" y="%d" style="fill:var(--ink)">%s</text>' % (ml + iw + 36, ly + 3, lab))
    o.append('</svg>')
    return "".join(o)

# --- entropy trajectory ---
ent = [("Thought MTE", "#5b7cfa", [mte(si, "t") for si in S]),
       ("Action MTE", "#1fb6a6", [mte(si, "a") for si in S])]
emax = max([v for _, _, ys in ent for v in ys if v is not None] + [0.4]) * 1.15
P.append('<h2 style="font-size:15px;font-weight:600;margin:22px 0 0">Uncertainty across the episode</h2>')
P.append('<div class="sub" style="margin:2px 0 4px">red-shaded steps = action not admissible or a repeated (action, obs) loop</div>')
P.append(svg_chart(ent, 0, emax, "Token entropy (MTE)", "↑ = more uncertain"))
# --- elicited-uncertainty trajectory (U = 1 - confidence; ↑ = uncertain, same as entropy) ---
if has_p:
    cf = [("U · P(True) thought", "#2f9e57", [unc(si, "ptrue", "thought") for si in S]),
          ("U · P(True) action", "#8fce9a", [unc(si, "ptrue", "action") for si in S]),
          ("U · verbalized thought", "#e0871e", [unc(si, "sep_verbalized", "thought") for si in S]),
          ("U · targeted u(q_t)", "#9b6cf0", [unc(si, "targeted", "thought") for si in S])]
    P.append(svg_chart(cf, 0, 1, "Elicited uncertainty (1 − confidence)", "↑ = more uncertain"))

# --- per-step detail table ---
P.append('<h2 style="font-size:15px;font-weight:600;margin:24px 0 0">Per-step detail</h2>')
P.append('<div style="font-size:11.5px;color:var(--muted);margin:2px 0 4px">'
         'every column is UNCERTAINTY (↑ = more uncertain): MTE = mean token entropy · '
         'U(P(T))=1−P(True) · U(Vrb)=1−verbalized · U(Tgt)=1−targeted u(q_t) · T=thought, A=action</div>')
P.append('<div style="overflow-x:auto">')
hdr = "<table><tr><th>step</th><th>action</th><th>adm</th><th>T·MTE</th><th>A·MTE</th>"
if has_p:
    hdr += "<th>T·U(PT)</th><th>A·U(PT)</th><th>T·U(Vrb)</th><th>A·U(Vrb)</th><th>T·U(Tgt)</th>"
P.append(hdr + "</tr>")
for si in S:
    tm, am = sd[si]
    st = steps.get(si, {})
    adm = st.get("in_admissible")
    row = ("<tr><td>%d</td><td class='a'>%s</td><td class='%s'>%s</td><td>%s</td><td>%s</td>"
           % (si, html.escape(str(st.get("action_parsed", ""))),
              "ok" if adm else "bad", "yes" if adm else "NO", f2(tm, "mte"), f2(am, "mte")))
    if has_p:
        row += ("<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                % (pval(si, "ptrue", "thought"), pval(si, "ptrue", "action"),
                   pval(si, "sep_verbalized", "thought"), pval(si, "sep_verbalized", "action"),
                   pval(si, "targeted", "thought")))
    P.append(row + "</tr>")
P.append("</table></div>")

# token heatmaps for the first 2 steps
P.append("<h1 style='font-size:16px;margin-top:26px'>Token-level entropy heatmap (first 2 steps)</h1>")
for si in sorted(by)[:2]:
    tm, am = stage_metrics(by[si])
    P.append('<div class="card"><div class="lbl">step %d · THOUGHT</div>%s</div>' % (si, heat(tm)))
    P.append('<div class="card"><div class="lbl">step %d · ACTION</div>%s</div>' % (si, heat(am)))

open(out, "w").write("\n".join(P))
print("wrote", out, "|", len(by), "steps |", len(calls), "calls")
