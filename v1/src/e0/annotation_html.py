"""E0 annotation page generator — one static, self-contained HTML file (spec E0.3: "a simple
static HTML page reading the JSONL, radio buttons, exports CSV. Do not build infrastructure").

Blindness: the page embeds NO judge labels and NO probe values. Annotators see the same rubric
text as the judge prompt, the full trajectory, and the highlighted target step — rendered
EXACTLY as the judge sees it (architecture-invariant: actions + observations, NO thoughts;
decision 2026-07-16 — kappa is only meaningful if humans and judge rate the same rendering).
Answers persist in localStorage; Export writes CSV (uid,label,note,annotator).
"""
from __future__ import annotations

import json

from src.agent.prompts import load_prompt
from src.e0.sample_steps import step_uid
from src.judge.pipeline import group_by_trajectory

_RUBRIC_START = "Labeling rules:"
_RUBRIC_END = "Now evaluate"

_PAGE = """<!doctype html>
<meta charset="utf-8">
<title>E0 step annotation</title>
<style>
 body{font:14px/1.5 -apple-system,sans-serif;max-width:900px;margin:2em auto;padding:0 1em}
 .rubric{background:#f6f6f6;border:1px solid #ddd;padding:1em;white-space:pre-wrap;font-size:13px}
 .step{padding:.4em .6em;border-left:3px solid #ddd;margin:.3em 0;white-space:pre-wrap}
 .target{border-left:3px solid #d33;background:#fff3f3}
 .nav{margin:1em 0;display:flex;gap:.6em;align-items:center}
 button{padding:.4em 1em} textarea{width:100%} .task{font-weight:600}
 .done{color:#2a7} .progress{margin-left:auto}
</style>
<h2>E0 step annotation</h2>
<p>Annotator: <input id="who" placeholder="your name" onchange="save()"></p>
<details open><summary>Rubric (same text the judge saw)</summary><div class="rubric">__RUBRIC__</div></details>
<div class="nav">
 <button onclick="go(-1)">&#8592; prev</button><button onclick="go(1)">next &#8594;</button>
 <span id="pos"></span><span class="progress" id="prog"></span>
</div>
<div class="task" id="task"></div>
<div id="traj"></div>
<p><b>Label the highlighted step:</b>
 <label><input type="radio" name="lab" value="1" onchange="save()"> 1 — good / helpful</label>
 <label><input type="radio" name="lab" value="0" onchange="save()"> 0 — bad</label></p>
<textarea id="note" rows="2" placeholder="optional note" onchange="save()"></textarea>
<div class="nav"><button onclick="exportCsv()">Export CSV</button></div>
<script>
const ITEMS = __ITEMS__;
let i = +(localStorage.getItem("e0_pos") || 0);
const store = k => JSON.parse(localStorage.getItem("e0_ans_" + k) || "{}");
function render(){
  const it = ITEMS[i];
  document.getElementById("pos").textContent = (i+1) + " / " + ITEMS.length;
  document.getElementById("task").textContent = "Task: " + it.task;
  document.getElementById("traj").innerHTML = it.steps.map((s, j) =>
    `<div class="step ${j===it.target ? "target" : ""}"><b>step ${j+1}</b>` +
    `\naction: ${esc(s.action)}\nobservation: ${esc(s.obs)}</div>`).join("");
  const a = store(it.uid);
  document.querySelectorAll('input[name="lab"]').forEach(r => r.checked = a.label === r.value);
  document.getElementById("note").value = a.note || "";
  const done = ITEMS.filter(x => store(x.uid).label !== undefined).length;
  document.getElementById("prog").innerHTML = `<span class="done">${done} answered</span>`;
}
function esc(s){const d=document.createElement("div");d.textContent=s;return d.innerHTML}
function save(){
  const it = ITEMS[i], sel = document.querySelector('input[name="lab"]:checked');
  localStorage.setItem("e0_ans_" + it.uid, JSON.stringify(
    {label: sel ? sel.value : undefined, note: document.getElementById("note").value}));
  localStorage.setItem("e0_who", document.getElementById("who").value); render();
}
function go(d){ i = Math.min(ITEMS.length-1, Math.max(0, i+d));
  localStorage.setItem("e0_pos", i); render(); }
function exportCsv(){
  const who = document.getElementById("who").value || "anon";
  const rows = [["uid","label","note","annotator"]];
  for (const it of ITEMS){ const a = store(it.uid);
    rows.push([it.uid, a.label ?? "", (a.note||"").replace(/"/g,"'"), who]); }
  const csv = rows.map(r => r.map(c => `"${c}"`).join(",")).join("\\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], {type:"text/csv"}));
  a.download = `e0_labels_${who}.csv`; a.click();
}
document.getElementById("who").value = localStorage.getItem("e0_who") || "";
render();
</script>
"""


def build_page(sampled_path: str, all_records_path: str, judge_prompt_path: str,
               out_html: str) -> dict:
    with open(sampled_path, encoding="utf-8") as f:
        sampled = [json.loads(line) for line in f if line.strip()]
    with open(all_records_path, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    trajs = group_by_trajectory(records)

    items = []
    for s in sampled:
        steps = trajs[(s["run_id"], s["task_id"])]
        items.append({
            "uid": step_uid(s),
            "task": (steps[0].get("extra") or {}).get("task", ""),
            "target": s["step_idx"],
            # architecture-invariant rendering, identical to the judge's: no thoughts
            "steps": [{"action": r["action_text"], "obs": r["observation_text"]}
                      for r in steps],
        })

    rubric = load_prompt(judge_prompt_path)
    lo, hi = rubric.find(_RUBRIC_START), rubric.find(_RUBRIC_END)
    if lo >= 0 and hi > lo:
        rubric = rubric[lo:hi].strip()

    html = _PAGE.replace("__RUBRIC__", rubric.replace("<", "&lt;"))
    html = html.replace("__ITEMS__", json.dumps(items, ensure_ascii=False))
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    return {"n_items": len(items), "out": out_html}
