# -*- coding: utf-8 -*-
# origin: new for V1.0 — EXP-ACQ + parity plots for the final report
"""Plots -> results/plots/. Run AFTER all metered work (matplotlib is
not free)."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np               # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "plots"
A = json.loads((HERE / "results/expacq/analysis.json").read_text(
    encoding="utf-8"))
TEAL, RUST, GREY, BLUE, PURP, GOLD = ("#0E6B5C", "#B4552D",
                                      "#666666", "#1f77b4",
                                      "#7b3f9e", "#b8860b")
ARM_STYLE = {
    "A0": (GREY, "o-", "A0 frozen (no acquisition)"),
    "A1": (GOLD, "v-", "A1 breeder"),
    "A2": (BLUE, "s-", "A2 miner (llama-8B)"),
    "A3": (PURP, "d-", "A3 breeder+miner (llama-8B)"),
    "A2-haiku": (RUST, "^-", "A2 miner (haiku)"),
    "A2-sonnet": (TEAL, "*-", "A2 miner (sonnet)"),
}


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=130)
    plt.close(fig)
    print("  ", name)


def main():
    # 1. the six learning curves
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for arm, (col, mk, lab) in ARM_STYLE.items():
        e = A["arms"].get(arm)
        if not e or not e["checkpoints"]:
            continue
        xs = [c["i"] for c in e["checkpoints"]]
        ys = [c["val_ok"] / c["val_n"] * 100
              for c in e["checkpoints"]]
        off = {"A0": 0, "A1": -0.15, "A2": 0.15, "A3": 0.3}.get(
            arm, 0)
        ax.plot(xs, [y + off * 0 for y in ys], mk, color=col,
                label=lab, ms=5)
    ax.set_xscale("log")
    ax.set_xlabel("traffic queries processed (identical replay)")
    ax.set_ylabel("frozen validation coverage (%)  [n=1000]")
    ax.set_title("EXP-ACQ learning curves — acquisition channel is "
                 "the only difference", fontsize=10)
    ax.legend(fontsize=8)
    ax.set_ylim(-0.4, 10)
    save(fig, "10_expacq_curves.png")

    # 2. sealed residual final + gate per arm
    fig, ax = plt.subplots(figsize=(9, 4.2))
    arms = [a for a in ARM_STYLE if a in A["arms"]
            and A["arms"][a].get("expacq_parse_sealed")]
    accs = [A["arms"][a]["expacq_parse_sealed"]["acc"] * 100
            for a in arms]
    gates = [A["arms"][a]["expacq_parse_sealed"]["gate_rate"] * 100
             for a in arms]
    xx = np.arange(len(arms))
    ax.bar(xx - 0.2, accs, 0.38, color=TEAL,
           label="sealed residual answered-correct (%)")
    ax.bar(xx + 0.2, gates, 0.38, color=RUST,
           label="wrong-fire (%)")
    ax.axhline(2.0, color=RUST, ls="--", lw=1)
    ax.set_xticks(xx)
    ax.set_xticklabels(arms, fontsize=8)
    ax.set_title("Sealed residual final (n=500): coverage bought, "
                 "gate held", fontsize=10)
    ax.legend(fontsize=8)
    save(fig, "11_sealed_final.png")

    # 3. candidate funnel per mining arm
    fig, ax = plt.subplots(figsize=(9, 4.2))
    marms = [a for a in ("A2", "A3", "A2-haiku", "A2-sonnet")
             if a in A["arms"]]
    stages = ("candidates_total", "cand_GATE_REJECTED",
              "cand_ACTIVE")
    labels = ("proposed", "gate-rejected", "ACTIVE")
    width = 0.25
    for i, (st, lab) in enumerate(zip(stages, labels)):
        vals = [A["arms"][a]["arm_stats"].get(st, 0) for a in marms]
        ax.bar(np.arange(len(marms)) + (i - 1) * width, vals,
               width, label=lab,
               color=(GREY, RUST, TEAL)[i])
    ax.set_xticks(np.arange(len(marms)))
    ax.set_xticklabels(marms, fontsize=8)
    ax.set_yscale("symlog")
    ax.set_title("The gauntlet funnel: proposed -> gated -> ACTIVE",
                 fontsize=10)
    ax.legend(fontsize=8)
    save(fig, "12_funnel.png")

    # 4. safety contrast: architecture vs pure LLMs on fresh sealed
    ctrl = HERE / "results" / "expacq" / "controls"

    def gate_of(tag, name):
        p = ctrl / f"ms_{name}_{tag}.jsonl"
        if not p.exists():
            return None
        rows = [json.loads(x) for x in
                p.read_text(encoding="utf-8").splitlines()]
        n = len(rows)
        wf = sum(1 for r in rows if r["expect"] == "answer"
                 and r["value"] is not None and not r["correct"]) \
            + sum(1 for r in rows if r["expect"] == "abstain"
                  and r["value"] is not None)
        return wf / n * 100 if n else None

    systems = [("engine+acq (sonnet arm)", 0.0, TEAL)]
    for tag, lab in (("K2", "engine, integrity OFF"),
                     ("K3-llama", "pure llama-8B"),
                     ("K3-haiku", "pure haiku"),
                     ("K3-sonnet", "pure sonnet")):
        g = gate_of(tag, "expacq_adv_sealed")
        if g is not None:
            systems.append((lab, g, RUST if g > 2 else GREY))
    fig, ax = plt.subplots(figsize=(9, 4.0))
    names = [s[0] for s in systems]
    vals = [s[1] for s in systems]
    cols = [s[2] for s in systems]
    ax.barh(np.arange(len(names)), vals, color=cols)
    ax.axvline(2.0, color=RUST, ls="--", lw=1)
    ax.set_yticks(np.arange(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("adversarial sealed wrong-fire (%)  "
                  "[n=122, dashed = the 2% gate]")
    ax.set_title("Safety contrast on the fresh adversarial final",
                 fontsize=10)
    save(fig, "13_safety_contrast.png")
    print("plots ->", OUT)


if __name__ == "__main__":
    main()
