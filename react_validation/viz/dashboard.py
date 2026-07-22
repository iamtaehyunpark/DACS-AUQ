"""UQ dashboard generator — reads the result files and writes one self-contained interactive
HTML (plotly inline; opens in any browser, offline). All metrics oriented as UNCERTAINTY
(higher = more uncertain). Run: python dashboard.py   ->  dashboard.html
"""
import json, math, os, statistics as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

os.chdir(os.path.dirname(os.path.abspath(__file__)))
DATA = "../data"
HARNESSES = ["decoupled", "entangled"]
COL = {"decoupled": "#3b6fe0", "entangled": "#e0872a"}
METRICS = [("thought_mte", "Thought entropy"), ("action_mte", "Action entropy"),
           ("U_ptrue_t", "Thought U·P(True)"), ("U_ptrue_a", "Action U·P(True)"),
           ("U_sep_verbalized_t", "Thought U·verbalized"), ("U_targeted_t", "Thought U·targeted")]
TYPE = {"pick_and_place": "put", "pick_clean_then_place": "clean", "pick_heat_then_place": "heat",
        "pick_cool_then_place": "cool", "look_at_obj": "examine", "pick_two_obj": "puttwo"}


def H(top):
    ps = [math.exp(a["logprob"]) for a in top]
    return -sum(p * math.log(p) for p in ps if p > 0)


def span_mte(gen, span):
    if not span:
        return None
    toks = gen[span[0]:span[1]]
    return sum(H(t["top"]) for t in toks) / len(toks) if toks else None


def ttype(tid):
    for k, v in TYPE.items():
        if (tid or "").startswith(k):
            return v
    return "?"


def load(h):
    steps, eps = {}, {}
    for line in open("%s/uq_%s_30.jsonl" % (DATA, h)):
        r = json.loads(line); k = r["kind"]
        if k == "call":
            d = steps.setdefault((r["task_id"], r["step_idx"]), {})
            g, sp = r["gen_logprobs"], r["spans"]
            if sp.get("thought"): d["thought_mte"] = span_mte(g, sp["thought"])
            if sp.get("action"): d["action_mte"] = span_mte(g, sp["action"])
        elif k == "step":
            d = steps.setdefault((r["task_id"], r["step_idx"]), {})
            d["action"] = r.get("action_parsed"); d["in_adm"] = r.get("in_admissible")
            d["loop"] = r.get("loop_flag")
        elif k == "episode":
            eps[r["task_id"]] = r
    for line in open("%s/probes_%s_30.jsonl" % (DATA, h)):
        r = json.loads(line)
        if r.get("kind") == "probe" and r.get("parse_ok"):
            d = steps.setdefault((r["task_id"], r["step_idx"]), {})
            d["U_%s_%s" % (r["probe_kind"], r["stage"][0])] = r.get("U")
    return steps, eps


DS = {h: load(h) for h in HARNESSES}
print("loaded:", {h: (len(DS[h][0]), len(DS[h][1])) for h in HARNESSES})


def rows(h):
    steps, eps = DS[h]
    for (tid, si), d in steps.items():
        r = dict(d); r["harness"] = h; r["task_id"] = tid; r["step"] = si
        r["type"] = ttype(tid); r["success"] = bool(eps.get(tid, {}).get("success"))
        yield r


ALL = [r for h in HARNESSES for r in rows(h)]


def col(rs, key):
    return [r[key] for r in rs if isinstance(r.get(key), (int, float))]


# ---------- figures ----------
figs = []

# 1) success rate by task type
f1 = go.Figure()
for h in HARNESSES:
    steps, eps = DS[h]
    by = {}
    for tid, e in eps.items():
        by.setdefault(ttype(tid), []).append(1 if e.get("success") else 0)
    types = ["put", "clean", "heat", "cool", "examine", "puttwo"]
    f1.add_bar(name=h, x=types, y=[100 * sum(by.get(t, [0])) / len(by[t]) if by.get(t) else 0 for t in types],
               marker_color=COL[h], text=[("%d/%d" % (sum(by.get(t, [])), len(by.get(t, [])))) if by.get(t) else "" for t in types])
tot = {h: (sum(1 for e in DS[h][1].values() if e.get("success")), len(DS[h][1])) for h in HARNESSES}
f1.update_layout(title="Task success by type  (decoupled %d/%d = %.0f%%,  entangled %d/%d = %.0f%%)"
                 % (tot["decoupled"][0], tot["decoupled"][1], 100 * tot["decoupled"][0] / tot["decoupled"][1],
                    tot["entangled"][0], tot["entangled"][1], 100 * tot["entangled"][0] / tot["entangled"][1]),
                 yaxis_title="success %", barmode="group", height=380)
figs.append(f1)

# 2) uncertainty metric distributions (box) per harness
f2 = go.Figure()
for h in HARNESSES:
    rs = [r for r in ALL if r["harness"] == h]
    for mk, ml in METRICS:
        f2.add_box(y=col(rs, mk), name=ml, legendgroup=h, offsetgroup=h,
                   marker_color=COL[h], boxpoints=False, showlegend=(mk == METRICS[0][0]))
f2.update_layout(title="Uncertainty metric distributions  (↑ = more uncertain)  ·  blue=decoupled, orange=entangled",
                 boxmode="group", height=430, yaxis_title="uncertainty")
figs.append(f2)

# 3) agreement: token entropy vs P(True)-uncertainty (thought stage), per step
f3 = go.Figure()
for h in HARNESSES:
    rs = [r for r in ALL if r["harness"] == h and isinstance(r.get("thought_mte"), (int, float)) and isinstance(r.get("U_ptrue_t"), (int, float))]
    f3.add_scatter(x=[r["thought_mte"] for r in rs], y=[r["U_ptrue_t"] for r in rs], mode="markers",
                   name=h, marker=dict(color=COL[h], size=5, opacity=0.45),
                   text=[("%s · step %d · %s" % (r["type"], r["step"], (r.get("action") or "")[:40])) for r in rs])
f3.update_layout(title="Do the signals agree? — thought token-entropy vs 1−P(True) (per step)",
                 xaxis_title="thought entropy (MTE)", yaxis_title="thought U·P(True) = 1−P(True)", height=430)
figs.append(f3)

# 4) does uncertainty flag trouble? admissible vs non-admissible steps
f4 = make_subplots(rows=1, cols=len(METRICS), subplot_titles=[m[1] for m in METRICS], horizontal_spacing=0.03)
for j, (mk, ml) in enumerate(METRICS, 1):
    ok = col([r for r in ALL if r.get("in_adm") is True], mk)
    bad = col([r for r in ALL if r.get("in_adm") is False], mk)
    f4.add_box(y=ok, name="admissible", marker_color="#2f9e57", legendgroup="ok", showlegend=(j == 1), row=1, col=j, boxpoints=False)
    f4.add_box(y=bad, name="not admissible", marker_color="#d1443e", legendgroup="bad", showlegend=(j == 1), row=1, col=j, boxpoints=False)
f4.update_layout(title="Does uncertainty flag trouble? — metric on admissible vs non-admissible actions", height=430)
figs.append(f4)

# 5) per-episode trajectory (dropdown over harness × episode)
f5 = go.Figure()
buttons = []
series = [("thought_mte", "Thought entropy", "#3b6fe0"), ("action_mte", "Action entropy", "#1fb6a6"),
          ("U_ptrue_t", "U·P(True) thought", "#2f9e57"), ("U_ptrue_a", "U·P(True) action", "#8fce9a"),
          ("U_sep_verbalized_t", "U·verbalized thought", "#e0872a"), ("U_targeted_t", "U·targeted", "#9b6cf0")]
epi_index = []
for h in HARNESSES:
    steps, eps = DS[h]
    for tid in sorted(eps):
        sis = sorted(si for (t, si) in steps if t == tid)
        epi_index.append((h, tid, sis))
for ei, (h, tid, sis) in enumerate(epi_index):
    steps = DS[h][0]
    for mk, ml, c in series:
        ys = [steps[(tid, si)].get(mk) for si in sis]
        f5.add_scatter(x=sis, y=ys, name=ml, line=dict(color=c), mode="lines+markers",
                       marker=dict(size=4), visible=(ei == 0),
                       text=[(steps[(tid, si)].get("action") or "") for si in sis])
n_series = len(series)
for ei, (h, tid, sis) in enumerate(epi_index):
    e = DS[h][1][tid]
    vis = [False] * (len(epi_index) * n_series)
    for k in range(n_series):
        vis[ei * n_series + k] = True
    buttons.append(dict(label="%s · %s · %s (%d steps)" % (h[:3], ttype(tid), "OK" if e.get("success") else "fail", e.get("n_steps", 0)),
                        method="update", args=[{"visible": vis}, {"title": "Episode: %s — %s (%s, %d steps)" % (h, tid.split("/")[0], "success" if e.get("success") else "fail", e.get("n_steps", 0))}]))
e0 = DS[epi_index[0][0]][1][epi_index[0][1]]
f5.update_layout(title="Episode: %s — %s" % (epi_index[0][0], epi_index[0][1].split("/")[0]),
                 updatemenus=[dict(buttons=buttons, x=0, xanchor="left", y=1.18, yanchor="top")],
                 xaxis_title="step", yaxis_title="uncertainty (↑)", height=460)
figs.append(f5)

# ---------- write self-contained HTML ----------
CSS = """<style>
body{font:15px/1.5 ui-sans-serif,system-ui,sans-serif;margin:0;padding:26px 30px;max-width:1180px;
 background:#0f1216;color:#e6eaf0}
h1{font-size:24px;margin:0 0 2px}.sub{color:#8b95a3;margin-bottom:20px}
.card{background:#161b22;border:1px solid #263040;border-radius:12px;padding:8px 10px;margin:16px 0}
.note{color:#8b95a3;font-size:13px;margin:2px 4px 8px}
</style>"""
head = ("<h1>Agentic UQ — result dashboard</h1>"
        "<div class='sub'>Qwen3.6-35B-A3B · ALFWorld · 30 episodes × decoupled &amp; entangled · "
        "Phase-1 entropy + Phase-2 probes (P(True), verbalized, targeted). Every metric = <b>uncertainty</b> "
        "(higher → more uncertain). Charts are interactive: hover for values, use the dropdown to pick an episode.</div>")
parts = ["<html><head><meta charset='utf-8'>", CSS, "</head><body>", head]
notes = ["", "", "points on the diagonal = the two signals agree; off-diagonal = they disagree on that step.",
         "if a metric is higher on non-admissible (red) than admissible (green) actions, it carries a usable trouble signal.",
         ""]
for i, fig in enumerate(figs):
    if notes[i]:
        parts.append("<div class='note'>%s</div>" % notes[i])
    parts.append("<div class='card'>" + pio.to_html(fig, full_html=False,
                 include_plotlyjs=("inline" if i == 0 else False),
                 config={"displayModeBar": False}) + "</div>")
parts.append("</body></html>")
open("dashboard.html", "w").write("\n".join(parts))
print("wrote dashboard.html  (%d bytes)" % os.path.getsize("dashboard.html"))
