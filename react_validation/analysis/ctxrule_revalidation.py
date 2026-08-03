"""Re-analysis of the tracked ctxrule n=300 step x condition matrix.

Everything here is computed from
  react_validation/reports/tables/ptrue_ctxrule_e1b_n300_matrix.csv
which is the only fully tracked, locally auditable per-step dataset in the repo.
"""
import numpy as np, pandas as pd
from itertools import combinations

CSV = "/Users/t/github/DACS-AUQ/react_validation/reports/tables/ptrue_ctxrule_e1b_n300_matrix.csv"
df = pd.read_csv(CSV)
CONDS = [c for c in df.columns if c.startswith("U_")]
PROD = "U_C3_R0"
rng = np.random.default_rng(0)


def auroc(y, s):
    y = np.asarray(y); s = np.asarray(s)
    n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = pd.Series(s).rank().values
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def clustered_boot(d, cols, B=10000):
    """returns dict col -> (auroc, lo, hi) and paired deltas vs PROD"""
    tasks = d["task_id"].unique()
    idx_by_task = {t: np.where(d["task_id"].values == t)[0] for t in tasks}
    base = {c: auroc(d["label"], d[c]) for c in cols}
    boots = {c: [] for c in cols}
    dboots = {c: [] for c in cols if c != PROD}
    for _ in range(B):
        pick = rng.choice(len(tasks), len(tasks), replace=True)
        rows = np.concatenate([idx_by_task[tasks[i]] for i in pick])
        sub = d.iloc[rows]
        y = sub["label"].values
        if y.sum() == 0 or y.sum() == len(y):
            continue
        a = {c: auroc(y, sub[c].values) for c in cols}
        for c in cols:
            boots[c].append(a[c])
        for c in dboots:
            dboots[c].append(a[c] - a[PROD])
    out = {}
    for c in cols:
        v = np.array(boots[c])
        out[c] = (base[c], np.percentile(v, 2.5), np.percentile(v, 97.5))
    dl = {}
    for c in dboots:
        v = np.array(dboots[c])
        dl[c] = (base[c] - base[PROD], np.percentile(v, 2.5), np.percentile(v, 97.5))
    return out, dl


def section(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


section("0. SAMPLE")
print(df.groupby(["label", "stratum"]).size())
print("n tasks (trajectories):", df.task_id.nunique(), " n steps:", len(df))
print("median step_idx  incorrect:", df[df.label == 1].step_idx.median(),
      " correct:", df[df.label == 0].step_idx.median())

section("1. FULL-SAMPLE AUROC + PAIRED DELTA vs PRODUCTION (reproduction check)")
a, dl = clustered_boot(df, CONDS)
print(f"{'cond':10} {'meanU_inc':>9} {'meanU_cor':>9} {'AUROC':>7} {'[95% CI]':>18} {'dAUROC vs prod':>26}")
for c in CONDS:
    mi = df.loc[df.label == 1, c].mean(); mc = df.loc[df.label == 0, c].mean()
    s = f"{c[2:]:10} {mi:9.3f} {mc:9.3f} {a[c][0]:7.3f} [{a[c][1]:.3f}, {a[c][2]:.3f}]"
    if c in dl:
        sig = "SIG" if (dl[c][1] > 0) or (dl[c][2] < 0) else "ns"
        s += f"   {dl[c][0]:+.3f} [{dl[c][1]:+.3f}, {dl[c][2]:+.3f}] {sig}"
    print(s)

section("2. LOOP-STRATIFIED DECOMPOSITION  (Paper-B section 8.iii, rung (b) analog)")
print("Does the evidence-grid gain survive when the degenerate (loop) error stratum is removed?\n")
subsets = {
    "ALL (150 inc / 150 cor)": df,
    "NON-LOOP errors only (72 inc / 150 cor)": df[~((df.label == 1) & (df.stratum == "loop"))],
    "LOOP errors only (78 inc / 150 cor)": df[~((df.label == 1) & (df.stratum != "loop"))],
    "NON-LOOP errors vs PLAIN correct": df[~((df.label == 1) & (df.stratum == "loop")) & ~((df.label == 0) & (df.stratum == "revisit"))],
}
key = ["U_C2_R0", PROD, "U_C5_R0", "U_C6_R0", "U_C3_R1", "U_C3_R2", "U_C3_R3"]
for name, d in subsets.items():
    aa, dd = clustered_boot(d, key, B=4000)
    print(f"--- {name}  (n={len(d)}, inc={int(d.label.sum())})")
    for c in key:
        s = f"    {c[2:]:8} AUROC {aa[c][0]:.3f} [{aa[c][1]:.3f}, {aa[c][2]:.3f}]"
        if c in dd:
            sig = "SIG" if (dd[c][1] > 0) or (dd[c][2] < 0) else "ns "
            s += f"   d {dd[c][0]:+.3f} [{dd[c][1]:+.3f}, {dd[c][2]:+.3f}] {sig}"
        print(s)

section("3. RULE FALSE-POSITIVE COST (rule-augmented judge vs decoy floor)")
for r, nm in [("U_C3_R1", "R1 generic"), ("U_C3_R2", "R2 targeted"), ("U_C3_R3", "R3 decoy")]:
    print(f"\n{nm}: median dU vs production by stratum")
    for st in ["loop", "other", "inadmissible", "revisit", "plain"]:
        m = df.stratum == st
        d = (df.loc[m, r] - df.loc[m, PROD])
        lab = "INCORRECT" if df.loc[m, "label"].iloc[0] == 1 else "correct  "
        print(f"   {st:13} {lab} n={m.sum():3}  median {d.median():+.3f}   frac_up {(d>0).mean():.2f}")

section("4. THRESHOLD TRANSFER ACROSS CONTEXTS (level shift -> recalibration need)")
y = df.label.values
def youden(s):
    ts = np.unique(s); best = (-1, None)
    for t in ts:
        p = (s >= t).astype(int)
        tpr = p[y == 1].mean(); fpr = p[y == 0].mean()
        if tpr - fpr > best[0]: best = (tpr - fpr, t)
    return best[1]
tprod = youden(df[PROD].values)
print(f"threshold tuned on production (C3/R0) at Youden J: U >= {tprod:.3f}")
print(f"{'cond':10} {'own-thresh bal.acc':>19} {'prod-thresh bal.acc':>20} {'loss':>7}")
for c in CONDS:
    s = df[c].values
    def bacc(t):
        p = (s >= t).astype(int)
        return 0.5 * (p[y == 1].mean() + (1 - p[y == 0]).mean())
    own = bacc(youden(s)); tr = bacc(tprod)
    print(f"{c[2:]:10} {own:19.3f} {tr:20.3f} {own-tr:+7.3f}")

section("5. RANK STABILITY BETWEEN CONTEXTS (Spearman rho of step scores)")
def spearman(a, b):
    return np.corrcoef(pd.Series(a).rank(), pd.Series(b).rank())[0, 1]
pairs = [(PROD, "U_C2_R0"), (PROD, "U_C4_R0"), (PROD, "U_C5_R0"), (PROD, "U_C6_R0"),
         (PROD, "U_C3_R1"), (PROD, "U_C3_R2"), (PROD, "U_C3_R3"),
         ("U_C5_R0", "U_C6_R0"), (PROD, "U_C0_R0")]
for x, z in pairs:
    print(f"   {x[2:]:8} vs {z[2:]:8}  rho {spearman(df[x],df[z]):+.3f}   "
          f"pearson {np.corrcoef(df[x],df[z])[0,1]:+.3f}")

section("5b. AUROC BY ERROR STRATUM (each error stratum vs all 150 correct steps)")
for st in ["loop", "other", "inadmissible"]:
    d = df[(df.label == 0) | ((df.label == 1) & (df.stratum == st))]
    vals = "  ".join(f"{c[2:]} {auroc(d.label, d[c]):.3f}" for c in
                     [PROD, "U_C5_R0", "U_C6_R0", "U_C3_R1", "U_C3_R2"])
    print(f"   {st:13} n_inc={int(d.label.sum()):3}  {vals}")

section("6. SAMPLE-EFFICIENCY OF THE THRESHOLD (how many labeled steps to fix a recipe)")
print("bal.acc of production probe using a threshold tuned on k random labeled steps,")
print("evaluated on the held-out remainder; 200 resamples per k.\n")
s = df[PROD].values
for k in [25, 50, 100, 150, 200]:
    accs = []
    for _ in range(200):
        idx = rng.choice(len(df), k, replace=False)
        hold = np.setdiff1d(np.arange(len(df)), idx)
        ss, yy = s[idx], y[idx]
        ts = np.unique(ss); best = (-1, None)
        for t in ts:
            p = (ss >= t).astype(int)
            if yy.sum() == 0 or yy.sum() == len(yy): continue
            j = p[yy == 1].mean() - p[yy == 0].mean()
            if j > best[0]: best = (j, t)
        p = (s[hold] >= best[1]).astype(int); yh = y[hold]
        accs.append(0.5 * (p[yh == 1].mean() + (1 - p[yh == 0]).mean()))
    full = (s >= tprod).astype(int)
    fullacc = 0.5 * (full[y == 1].mean() + (1 - full[y == 0]).mean())
    print(f"   k={k:4}  held-out bal.acc {np.mean(accs):.3f} +- {np.std(accs):.3f}   "
          f"({100*np.mean(accs)/fullacc:.1f}% of the all-300-step-tuned {fullacc:.3f})")
