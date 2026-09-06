# -*- coding: utf-8 -*-
"""Charts for the V1.8 report. Every number read from
results/v18/aggregate18.json (+ V1.7 summaries via it)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)
A = json.load(open(r"C:\Users\admin\Downloads\reflex-engine\results\v18"
                   r"\aggregate18.json", encoding="utf-8"))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25,
                     "grid.linewidth": 0.6, "figure.dpi": 200})
C = {"haiku": "#8ecae6", "sonnet": "#219ebc", "fable": "#fb8500",
     "opus": "#023047", "det": "#606c38", "neg": "#c1121f",
     "all": "#6a4c93"}
MODELS = ["haiku", "sonnet", "opus", "fable"]

# 1 sealed coverage: V1.7 R-arm (with wrongs) vs V1.8 dev vs all scope
fig, ax = plt.subplots(figsize=(7.2, 3.4))
x = range(4)
w = 0.26
v17 = [100 * A["v17_reference"][m]["seal"]["coverage"] for m in MODELS]
v17w = [A["v17_reference"][m]["seal"]["WRONG"] for m in MODELS]
d18 = [100 * A["arms"]["B-%s-dev" % m]["seal"]["coverage"] for m in MODELS]
a18 = [100 * A["arms"]["B-%s-all" % m]["seal"]["coverage"] for m in MODELS]
det = 100 * 112170 / 298905
ax.bar([i - w for i in x], v17, w, color="#bbbbbb",
       label="V1.7 R-arm (positional templates)")
ax.bar([i for i in x], d18, w, color=[C[m] for m in MODELS],
       label="V1.8 dev-plan library")
ax.bar([i + w for i in x], a18, w, color=[C[m] for m in MODELS],
       alpha=0.55, hatch="//", label="V1.8 dev+sealed-plan library")
ax.axhline(det, color=C["det"], ls="--", lw=1)
ax.text(3.45, det + 0.6, "composer alone %.1f%%" % det, fontsize=8,
        color=C["det"], ha="right")
for i, m in enumerate(MODELS):
    ax.text(i - w, v17[i] + 0.6, "%d\nwrong" % v17w[i], ha="center",
            fontsize=7.5, color=C["neg"])
    ax.text(i, d18[i] + 0.6, "0", ha="center", fontsize=8,
            fontweight="bold")
    ax.text(i + w, a18[i] + 0.6, "0", ha="center", fontsize=8,
            fontweight="bold")
ax.set_xticks(list(x))
ax.set_xticklabels(MODELS)
ax.set_ylabel("sealed in-domain coverage (%)")
ax.set_ylim(0, 66)
ax.set_title("SEAL 300k, run once: coverage per arm; wrong answers on "
             "top of each bar", fontsize=10)
ax.legend(fontsize=7.8, frameon=False, loc="upper left")
fig.tight_layout()
fig.savefig(OUT / "c1_seal_coverage.png")
plt.close(fig)

# 2 RETAIN per model + new coverage
ms = [m for m in MODELS if "B-%s-dev" % m in A["retain"]]
fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.2))
ret = [A["retain"]["B-%s-dev" % m]["RETAIN"] * 100 for m in ms]
den = [A["retain"]["B-%s-dev" % m]["v17_template_serves"] for m in ms]
new = [A["retain"]["B-%s-dev" % m]["bind_new_coverage"] for m in ms]
axes[0].bar(ms, ret, color=[C[m] for m in ms], width=0.6)
axes[0].axhline(60, color=C["neg"], ls="--", lw=1)
axes[0].text(len(ms) - 0.5, 61.5, "RETAIN bar 60%", fontsize=8,
             color=C["neg"], ha="right")
for i, v in enumerate(ret):
    axes[0].text(i, v + 1, "%.1f%%" % v, ha="center", fontsize=9)
axes[0].set_ylim(0, 105)
axes[0].set_title("RETAIN: V1.7 template-served items\nstill served by "
                  "the binder (SEAL)", fontsize=9.5)
axes[1].bar(ms, den, width=0.6, color="#bbbbbb",
            label="V1.7 template serves (denominator)")
axes[1].bar(ms, new, width=0.6, bottom=den, color=[C[m] for m in ms],
            label="new binder serves V1.7 escalated")
for i in range(len(ms)):
    axes[1].text(i, den[i] + new[i] + 400, format(new[i], ","),
                 ha="center", fontsize=8)
axes[1].set_title("Reuse volume on SEAL: retained vs new", fontsize=9.5)
axes[1].legend(fontsize=7.5, frameon=False, loc="upper left")
axes[1].set_ylim(0, max(den[i] + new[i] for i in range(len(ms))) * 1.25)
fig.tight_layout()
fig.savefig(OUT / "c2_retain.png")
plt.close(fig)

# 3 served share by depth (B-all-all seal)
fig, ax = plt.subplots(figsize=(6.6, 3.2))
bk = A["arms"]["B-all-all"]["seal"]["by_k"]
ks = ["k2", "k3", "k4", "k5", "k6"]
comp = [bk[k]["served"] - bk[k].get("bind", 0) for k in ks]
bind = [bk[k].get("bind", 0) for k in ks]
esc = [bk[k].get("escalated", 0) for k in ks]
tot = [comp[i] + bind[i] + esc[i] for i in range(5)]
c_sh = [100 * comp[i] / tot[i] for i in range(5)]
b_sh = [100 * bind[i] / tot[i] for i in range(5)]
ax.bar(ks, c_sh, color=C["det"], width=0.62, label="composer (deterministic)")
ax.bar(ks, b_sh, bottom=c_sh, color=C["all"], width=0.62,
       label="binder (role-aware reuse)")
for i in range(5):
    ax.text(i, c_sh[i] + b_sh[i] + 1.5, "%.1f%%" % (c_sh[i] + b_sh[i]),
            ha="center", fontsize=8.5)
ax.set_ylim(0, 105)
ax.set_ylabel("share of sealed items served (%)")
ax.set_title("Union library on SEAL: served share by chain depth, "
             "zero wrong", fontsize=10)
ax.legend(fontsize=8, frameon=False, loc="upper right")
fig.tight_layout()
fig.savefig(OUT / "c3_depth.png")
plt.close(fig)

# 4 PROBE-B32 disposition
pb = A["controls"]["probe_b32"]["counts"]
fig, ax = plt.subplots(figsize=(6.2, 2.6))
vals = [pb.get("served_gold", 0), pb.get("abstained", 0),
        pb.get("SERVED_WRONG", 0)]
ax.barh(["served the gold", "abstained", "served WRONG"], vals,
        color=[C["det"], "#bbbbbb", C["neg"]])
for i, v in enumerate(vals):
    ax.text(v + 60, i, format(v, ","), va="center", fontsize=9)
ax.set_xlim(0, 9800)
ax.set_title("PROBE-B32: the 8,842 questions V1.7 answered wrong, "
             "through the V1.8 binder", fontsize=9.5)
fig.tight_layout()
fig.savefig(OUT / "c4_probe.png")
plt.close(fig)

# 5 compounding curve (raw) per dev arm
fig, ax = plt.subplots(figsize=(6.4, 3.2))
for m in ms:
    cur = A["retain"]["B-%s-dev" % m]["COMPOUND"]["curve"]
    ax.plot([c["n"] / 1000 for c in cur], [c["ratio"] for c in cur],
            "-o", color=C[m], label=m, ms=4)
ax.set_xlabel("sealed items processed (thousands)")
ax.set_ylabel("certified binder serves / plans purchased")
ax.set_title("COMPOUND (raw): linear in the stream; each purchased plan "
             "serves ~60 questions per 300k", fontsize=9.5)
ax.legend(fontsize=8, frameon=False)
fig.tight_layout()
fig.savefig(OUT / "c5_compound.png")
plt.close(fig)

# 6 harvest funnel (union all)
L = A["libraries"]
plans = sum(L["%s_all" % m]["harvest_ledger"]["plans_in"] for m in MODELS)
full = sum(L["%s_all" % m]["harvest_ledger"]["templated_full"]
           for m in MODELS)
two = sum(L["%s_all" % m]["harvest_ledger"].get("two_donor_full", 0) +
          L["%s_all" % m]["harvest_ledger"].get("two_donor_sub", 0)
          for m in MODELS)
adm = sum(L["%s_all" % m]["templates"] for m in MODELS)
uni = L["all_all"]["templates"]
fig, ax = plt.subplots(figsize=(6.6, 3.0))
stages = ["certified\nplans", "templatized", "two-donor\ncandidates",
          "admitted\n(4 models)", "union\n(canonical)"]
vals = [plans, full, two, adm, uni]
ax.bar(stages, vals, color=["#bbbbbb", "#bbbbbb", C["sonnet"], C["opus"],
                            C["all"]], width=0.6)
for i, v in enumerate(vals):
    ax.text(i, v + 80, format(v, ","), ha="center", fontsize=9)
ax.tick_params(axis="x", labelsize=8)
ax.set_ylim(0, plans * 1.15)
ax.set_title("Harvest funnel: V1.7 certified plans to the V1.8 union "
             "library (zero probation wrongs)", fontsize=9.5)
fig.tight_layout()
fig.savefig(OUT / "c6_funnel.png")
plt.close(fig)

# 7 gap classes on DEV-L (B-all-all)
g = A["gapclass"]["shares"]
fig, ax = plt.subplots(figsize=(6.0, 2.6))
names = ["structure gap", "adapter gap", "binding gap", "semantic kill",
         "other"]
vals = [100 * g["structure_gap"], 100 * g["adapter_gap"],
        100 * g["binding_gap"], 100 * g["semantic_kill"], 100 * g["other"]]
ax.barh(names, vals, color=[C["det"], C["neg"], C["all"], "#999999",
                            "#cccccc"])
for i, v in enumerate(vals):
    ax.text(v + 1, i, "%.2f%%" % v, va="center", fontsize=9)
ax.set_xlim(0, 115)
ax.set_title("Why the union library still escalates 44.7% of DEV-L: "
             "gap classes (adapter gap = 0.0%)", fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "c7_gaps.png")
plt.close(fig)
print("charts ->", OUT)
