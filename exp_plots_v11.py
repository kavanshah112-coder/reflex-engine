# -*- coding: utf-8 -*-
# origin: new for V1.1 — report plots
"""V1.1 plots -> results/plots/2x_*.png"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np               # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "plots"
TEAL, RUST, GREY, BLUE, PURP, GOLD = ("#0E6B5C", "#B4552D",
                                      "#666666", "#1f77b4",
                                      "#7b3f9e", "#b8860b")


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=130)
    plt.close(fig)
    print("  ", name)


def main():
    # 20: the commercial 100k curve (serve mix + window coverage)
    cks = [json.loads(l) for l in
           (HERE / "results/expacq11/sim/checkpoints.jsonl")
           .read_text(encoding="utf-8").splitlines()]
    xs = [c["i"] for c in cks]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.3))
    det = [c["covered_det"] / c["i"] * 100 for c in cks]
    txt = [c["covered_text"] / c["i"] * 100 for c in cks]
    mem = [c["covered_memory"] / c["i"] * 100 for c in cks]
    esc = [(c["esc_priced"] + c["esc_executed"]) / c["i"] * 100
           for c in cks]
    ax[0].stackplot(xs, det, mem, txt, esc,
                    colors=[TEAL, GOLD, BLUE, GREY],
                    labels=["deterministic", "MEMORY.fact",
                            "TEXT.qa", "escalated (priced)"])
    ax[0].set_ylim(80, 100.5)
    ax[0].set_xlabel("queries processed")
    ax[0].set_ylabel("cumulative share of stream (%)")
    ax[0].set_title("100k varied-topic stream: who answers",
                    fontsize=10)
    ax[0].legend(fontsize=7, loc="lower right")
    wc = [c["window_cov"] * 100 for c in cks]
    ax[1].plot(xs, wc, "o-", color=TEAL,
               label="10k-window coverage")
    ax[1].plot(xs, [c["window_wrong"] for c in cks], "s--",
               color=RUST, label="window wrong answers")
    ax[1].set_xlabel("queries processed")
    ax[1].set_ylabel("%  /  count")
    ax[1].set_title("Coverage climbs as reflexes mint; wrong "
                    "answers stay at zero", fontsize=10)
    ax[1].legend(fontsize=8)
    save(fig, "20_commercial_curve.png")

    # 21: scale comparison
    sc = json.loads((HERE / "results/expacq11/scale/"
                     "scale_analysis.json").read_text(
        encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(8.5, 4.0))
    models = ["haiku", "sonnet", "opus"]
    strict = [sc["models"][m]["strict_equality"] for m in models]
    agree = [sc["models"][m]["content_agreement"] for m in models]
    corr = [sc["models"][m]["all3_correct"] for m in models]
    xx = np.arange(3)
    ax.bar(xx - 0.25, corr, 0.23, color=TEAL,
           label="all 3 runs correct")
    ax.bar(xx, agree, 0.23, color=GOLD, label="content agreement")
    ax.bar(xx + 0.25, strict, 0.23, color=PURP,
           label="strict equality (prod TEXT.qa gate)")
    ax.set_xticks(xx)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 21)
    ax.set_ylabel("questions (of 20)")
    ax.set_title("TEXT-reflex quality vs answering-model scale "
                 "(3 independent runs x 20 questions, bridge)",
                 fontsize=10)
    ax.legend(fontsize=8)
    save(fig, "21_scale_comparison.png")

    # 22: the arc's held-out parser coverage across versions
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    vers = ["V0.10\n(breeder)", "V0.11\n(semantic)",
            "V1.0\n(+sonnet acq)", "V1.1\n(engine fixes)"]
    # V1.0 overall = 84.2 + 7.2% of the 15.8pp residual = 85.3
    vals = [12.8, 84.2, 85.3, 100.0]
    cols = [GREY, BLUE, GOLD, TEAL]
    ax.bar(np.arange(4), vals, color=cols)
    for i, v in enumerate(vals):
        ax.text(i, v + 1, f"{v:g}%", ha="center", fontsize=9)
    ax.set_ylim(0, 108)
    ax.set_ylabel("held-out parser coverage (%)")
    ax.set_title("The coverage arc (sealed, wrong-fire 0.000 at "
                 "every step)", fontsize=10)
    save(fig, "22_coverage_arc.png")

    # 23: commercial energy model
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    e = json.loads((HERE / "results/expacq11/"
                    "engine_energy_sample.json").read_text(
        encoding="utf-8"))
    jq = e["j_query"]
    served, priced = 95472, 4468
    j_v11 = served * jq + priced * 1910.0
    j_llm = 100000 * 1910.0
    ax.bar([0, 1], [j_llm / 3.6e6, j_v11 / 3.6e6],
           color=[GREY, TEAL])
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["pure LLM\n(measured 1910 J/q)",
                        f"reflex engine\n({jq:.1f} J/q certified + "
                        f"priced escalations)"])
    ax.set_ylabel("kWh per 100k queries")
    for i, v in enumerate([j_llm / 3.6e6, j_v11 / 3.6e6]):
        ax.text(i, v, f"{v:.2f} kWh", ha="center", va="bottom",
                fontsize=9)
    ax.set_title(f"Commercial energy: {100*(1-j_v11/j_llm):.1f}% "
                 "saving on the measured 100k mix", fontsize=10)
    save(fig, "23_commercial_energy.png")
    print("plots done")


if __name__ == "__main__":
    main()
