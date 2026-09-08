# -*- coding: utf-8 -*-
"""V1.9 final report (MD + PDF) from results/v19/M-*_summary.json (one-model arms)."""
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (HRFlowable, Image, Paragraph,
                                SimpleDocTemplate, Spacer, Table,
                                TableStyle)

HERE = Path(__file__).parent
CH = HERE / "charts19v"
CH.mkdir(exist_ok=True)
REPO = Path(r"C:\Users\admin\Downloads\reflex-engine")
OUT = REPO / "results" / "v19"
ORDER = ["sonnet", "opus", "haiku", "fable"]

# post-hoc classes of every by-gold A2 wrong (ledger notes V3-V5, V7); nothing relabelled
CLASS = {
    "a0375": "gold errata", "a1349": "gold errata", "g0454": "gold errata",
    "a1332": "gold format", "a1327": "gold format", "a1495": "gold format",
    "a1979": "rounding", "a1983": "rounding", "a1984": "rounding", "a1989": "rounding",
    "a0175": "unit convention", "a0185": "unit convention",
    "a1412": "convention", "g0012": "convention", "g1161": "convention", "a2261": "convention", "a2105": "convention",
    "g1035": "GENUINE", "g0790": "GENUINE", "g0796": "GENUINE",
}


def load(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


arms = {m: load(OUT / ("M-%s_sealed_summary.json" % m)) for m in ORDER}
arms = {m: v for m, v in arms.items() if v}
dev = load(OUT / "M-sonnet_dev_summary.json")
purity = load(OUT / "purity_M-sonnet_dev.json")
reuse = {m: load(OUT / ("reuse_M-%s.json" % m)) for m in ORDER}
reuse = {m: v for m, v in reuse.items() if v}
ctrl = load(OUT / "controls19v.json")
ledger = (REPO / "bug_audit_v1_9.md").read_text(encoding="utf-8")


def pct(x):
    return "—" if x is None else "%.1f%%" % (100 * x)


def genuine(v):
    return sorted(i for i in v["admission"]["A2"]["wrong_ids"] if CLASS.get(i, "unclassified") == "GENUINE")


def unclassified(v):
    return sorted(i for i in v["admission"]["A2"]["wrong_ids"] if i not in CLASS)


def _gates_removed(v):
    return len(set(v["admission"]["A0"]["wrong_ids"]) - set(v["admission"]["A2"]["wrong_ids"]))


def _own_removed(v):
    return len(set(v["admission"]["A1"]["wrong_ids"]) - set(v["admission"]["A2"]["wrong_ids"]))


def errata_only(v):
    return all(CLASS.get(i) in ("gold errata", "gold format") for i in v["admission"]["A2"]["wrong_ids"])


# ---------------------------------------------------------------- ladder (primary = M-sonnet)
pri = arms.get("sonnet")
if pri is None:
    letter_ = "?"
else:
    a2 = pri["admission"]["A2"]
    gen = len(genuine(pri))
    fa = a2["FALSE_ADMIT"]
    reach = pri["REACH"]
    gc = pri["GATE_COST"]
    ru = reuse.get("sonnet") or {}
    if not (ctrl or {}).get("pass"):
        letter_ = "F"
    elif gen > 0:
        letter_ = "E"
    elif reach < 0.30 or gc > 0.30:
        letter_ = "D"
    elif fa > 0.005 and errata_only(pri):
        letter_ = "C"
    elif fa > 0.005:
        letter_ = "C"  # by-gold bar fails on non-errata classes too; the letter can go no higher
    elif ru.get("REUSE_WRONG", 1) > 0 or ru.get("REUSE_SERVED", 0) == 0:
        letter_ = "B"
    else:
        letter_ = "A"

# ---------------------------------------------------------------- charts
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 200})
C = {"reach": "#219ebc", "q": "#606c38", "fa": "#c1121f", "ans": "#fb8500", "gen": "#7b2cbf", "grey": "#bbbbbb"}
ms = [m for m in ORDER if m in arms]
if ms:
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    x = range(len(ms))
    w = 0.2
    ax.bar([i - 1.5 * w for i in x], [100 * arms[m]["REACH"] for m in ms], w, color=C["reach"], label="REACH")
    ax.bar([i - 0.5 * w for i in x], [100 * arms[m]["READING_CORRECT"] for m in ms], w, color=C["q"], label="READING-CORRECT")
    ax.bar([i + 0.5 * w for i in x], [100 * arms[m]["ANSWER_CORRECT"] for m in ms], w, color=C["ans"], label="own answer correct")
    ax.bar([i + 1.5 * w for i in x], [100 * arms[m]["admission"]["A2"]["FALSE_ADMIT"] for m in ms], w, color=C["fa"], label="A2 FALSE-ADMIT (gold)")
    for i, m in enumerate(ms):
        a = arms[m]["admission"]["A2"]
        ax.text(i + 1.5 * w, 100 * a["FALSE_ADMIT"] + 1.5, "%d/%d\ngen %d" % (a["wrong_by_gold"], a["admitted"], len(genuine(arms[m]))), ha="center", fontsize=7, color=C["fa"])
    ax.axhline(0.5, color=C["fa"], ls=":", lw=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(["M-" + m for m in ms])
    ax.set_ylabel("%")
    ax.set_ylim(0, 108)
    ax.set_title("SEALED 1,764, one model per arm: reach, reading quality, own-answer accuracy, A2 false admission", fontsize=9)
    ax.legend(fontsize=7.5, frameon=False, ncol=4, loc="upper center")
    fig.tight_layout()
    fig.savefig(CH / "v1_arms.png")
    plt.close(fig)

    fig, axs = plt.subplots(1, len(ms), figsize=(7.4, 2.6), sharey=True)
    if len(ms) == 1:
        axs = [axs]
    for ax, m in zip(axs, ms):
        ad = arms[m]["admission"]
        rules = ["A0", "A1", "A2"]
        ax.bar(rules, [ad[r]["admitted"] for r in rules], color=C["grey"], label="admitted")
        ax.bar(rules, [ad[r]["wrong_by_gold"] for r in rules], color=C["fa"], label="wrong by gold")
        for i, r in enumerate(rules):
            ax.text(i, ad[r]["admitted"] + 15, "%d\n%d wrong" % (ad[r]["admitted"], ad[r]["wrong_by_gold"]), ha="center", fontsize=7)
        ax.set_title("M-" + m, fontsize=9)
        ax.set_ylim(0, 1350)
    axs[0].set_ylabel("items")
    axs[0].legend(fontsize=7, frameon=False, loc="upper right")
    fig.suptitle("Admission rules: A0 agreement only · A1 engine only (G-P6 + rules) · A2 both", fontsize=9)
    fig.tight_layout()
    fig.savefig(CH / "v2_rules.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.4, 2.5))
    keys = ["G-P6", "S-INT", "S-RATIO", "S-PCT", "S-GEOM"]
    w = 0.8 / len(ms)
    for j, m in enumerate(ms):
        v = arms[m]
        vals = [100 * v["G6"]["false_abstain_rate"]] + [100 * v["rules"][k]["false_abstain_rate"] for k in keys[1:]]
        ax.bar([i + (j - (len(ms) - 1) / 2) * w for i in range(len(keys))], vals, w, label="M-" + m)
    ax.axhline(3, color=C["fa"], ls=":", lw=0.8)
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels(keys)
    ax.set_ylabel("false abstention, % of executed")
    ax.set_title("What honesty costs: kills of CORRECT readings per gate (dotted: 3% RULES bar; G-P6 has no bar)", fontsize=9)
    ax.legend(fontsize=7.5, frameon=False, ncol=4)
    fig.tight_layout()
    fig.savefig(CH / "v3_cost.png")
    plt.close(fig)

if reuse:
    rm = [m for m in ORDER if m in reuse]
    fig, ax = plt.subplots(figsize=(6.4, 2.4))
    ax.bar(rm, [reuse[m]["REUSE_SERVED"] for m in rm], color=C["grey"], label="would-serve")
    ax.bar(rm, [reuse[m]["REUSE_WRONG"] for m in rm], color=C["fa"], label="WRONG")
    for i, m in enumerate(rm):
        ax.text(i, reuse[m]["REUSE_SERVED"] + 2, "%d served / %d wrong" % (reuse[m]["REUSE_SERVED"], reuse[m]["REUSE_WRONG"]), ha="center", fontsize=8)
    ax.set_title("Cue-keyed reuse, measured and never served: SEALED items bound to another item's admitted reading", fontsize=8.5)
    ax.legend(fontsize=7.5, frameon=False)
    fig.tight_layout()
    fig.savefig(CH / "v4_reuse.png")
    plt.close(fig)

# ---------------------------------------------------------------- markdown
md = []
md.append("# V1.9 FINAL REPORT — One-Model Reading Reflexes with Escalation Feedback (branch v1.9-reading)\n")
md.append("**Pre-registered outcome: %s** on the frozen ladder (`V19_SPEC.md` §10, tag `v1.9-plan` @ 209bba7).\n" % letter_)
md.append("## Headline\n")
if pri:
    a2 = pri["admission"]["A2"]
    g = genuine(pri)
    md.append("- **Primary arm M-sonnet (sonnet answers AND proposes), SEALED 1,764 never-sampled items, run once:** REACH %s (%d executable readings), READING-CORRECT %s, own answer correct %s; A2 admitted %d, **FALSE-ADMIT by gold %d (%s)**, of which **GENUINE %d** (%s). SAFETY-GEN %s."
              % (pct(pri["REACH"]), pri["status"]["executed"], pct(pri["READING_CORRECT"]), pct(pri["ANSWER_CORRECT"]), a2["admitted"], a2["wrong_by_gold"], pct(a2["FALSE_ADMIT"]), len(g), ", ".join(g) or "none", "**fails by one item**" if g else "holds"))
for m in ("opus", "haiku", "fable"):
    if m in arms:
        v = arms[m]
        a2 = v["admission"]["A2"]
        g = genuine(v)
        md.append("- **M-%s:** REACH %s, READING-CORRECT %s, own answer %s; A2 %d admitted / %d wrong by gold (%s) / **%d genuine** (%s)."
                  % (m, pct(v["REACH"]), pct(v["READING_CORRECT"]), pct(v["ANSWER_CORRECT"]), a2["admitted"], a2["wrong_by_gold"], pct(a2["FALSE_ADMIT"]), len(g), ", ".join(g) or "none"))
    else:
        md.append("- **M-%s:** not scored (see §6)." % m)
md.append("- **Negative, prominent:** the engine-side honesty gates (G-P6 + S-INT/RATIO/PCT/GEOM) removed %s of the by-gold wrongs that agreement alone (A0) would have admitted, while killing %s of A0's admissions; every wrong they did remove was on haiku. G-P6 killed %s readings of which %s were correct. The filter that carries the safety is the model's own answer (A1→A2 removes %s wrongs)." % (", ".join("%d/%d" % (_gates_removed(arms[m]), arms[m]["admission"]["A0"]["wrong_by_gold"]) for m in ms), ", ".join("%d%%" % round(100 * (1 - arms[m]["admission"]["A2"]["admitted"] / arms[m]["admission"]["A0"]["admitted"])) for m in ms), ", ".join(str(arms[m]["G6"]["kills"]) for m in ms), ", ".join(str(arms[m]["G6"]["kills_of_correct"]) for m in ms), ", ".join(str(_own_removed(arms[m])) for m in ms)))
if reuse:
    md.append("- **Reuse (measured, never served):** " + "; ".join("M-%s %d would-serve / **%d wrong**" % (m, reuse[m]["REUSE_SERVED"], reuse[m]["REUSE_WRONG"]) for m in ORDER if m in reuse) + ". Cue-keyed reuse is unsafe on natural text; ladder A is out on every arm.")
if purity:
    md.append("- **CUE-PURITY (DEV, sonnet):** %s (%d pure of %d keys with ≥2 readings; %d singleton keys)." % (pct(purity["CUE_PURITY"]), purity["pure_keys"], purity["keys_with_2plus_readings"], purity["singular_keys"]))
md.append("- **GATE-CTRL:** %s (%d checks).\n" % ("PASS" if (ctrl or {}).get("pass") else "FAIL", sum(1 for k, v in (ctrl or {}).items() if v is True)))

md.append("## 1. What was run\n")
md.append("V1.9 asks whether ONE model — the same model that answers the escalated question — can propose a READING (a plan over the question's stated numbers as positional slots plus structural constants) that the engine admits with zero genuine wrong admissions, the engine carrying the safety. S1 (the pre-study, tag `s1-final`) had shown that agreement between an engine-computed reading and a *second* model's answer admits ~1.1% wrong by gold; the user ruled out a second model, so V1.9 replaces it with three engine-side gates plus the model's own answer: **G-P6 lexical honesty** (word quantities, plural named agents, cardinality matching), four **structural abstentions** (S-INT, S-RATIO, S-PCT, S-GEOM), and **A2 = engine gates + agreement with the model's own answer**. Two weaker rules are reported alongside: A0 (agreement only, S1's rule) and A1 (engine gates only, no agreement).\n")
md.append("The sealed set is 1,764 GSM8K-test and ASDiv items never sampled by S1 (sha256 in `results/v19/data/`), in 71 batches of 25. Four arms, one model each, both roles: sonnet (primary), opus, haiku, fable. Every proposer and answerer ran as a bridge agent with Read/Write only, saw only the batch file (question text + numbers), never the golds, never the engine. Readings were bound, gated through the V1.8 stack in reading mode, executed by the witness, and graded against the corpus gold offline. DEV (S1's 1,800 items with sonnet's S1 readings and fresh sonnet answers) was used to set G-P6 and the rules before the sealed run; SEALED was scored once per arm.\n")

md.append("## 2. Results per arm (SEALED 1,764, run once)\n")
md.append("| arm | executed (REACH) | reading correct | own answer correct | G-P6 kills (false-abstain) | rule kills S-INT/RATIO/PCT/GEOM | GATE-COST | A0 adm/wrong | A1 adm/wrong | **A2 adm/wrong (FA)** | **genuine** | A2 rejected-but-correct |")
md.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for m in ms:
    v = arms[m]
    ad = v["admission"]
    r = v["rules"]
    md.append("| M-%s | %d (%s) | %s | %s | %d (%s) | %d/%d/%d/%d | %s | %d/%d | %d/%d | **%d/%d (%s)** | **%d** | %d |"
              % (m, v["status"]["executed"], pct(v["REACH"]), pct(v["READING_CORRECT"]), pct(v["ANSWER_CORRECT"]), v["G6"]["kills"], pct(v["G6"]["false_abstain_rate"]),
                 r["S-INT"]["kills"], r["S-RATIO"]["kills"], r["S-PCT"]["kills"], r["S-GEOM"]["kills"], pct(v["GATE_COST"]),
                 ad["A0"]["admitted"], ad["A0"]["wrong_by_gold"], ad["A1"]["admitted"], ad["A1"]["wrong_by_gold"], ad["A2"]["admitted"], ad["A2"]["wrong_by_gold"], pct(ad["A2"]["FALSE_ADMIT"]), len(genuine(v)), v["A2_rejected_correct"]))
md.append("")
if dev:
    ad = dev["admission"]
    md.append("DEV 1,800 (M-sonnet, for the record; used to set the gates): REACH %s, READING-CORRECT %s, own answer %s, A0 %d/%d, A1 %d/%d, A2 %d/%d (%s), GATE-COST %s, G-P6 false-abstain %s.\n"
              % (pct(dev["REACH"]), pct(dev["READING_CORRECT"]), pct(dev["ANSWER_CORRECT"]), ad["A0"]["admitted"], ad["A0"]["wrong_by_gold"], ad["A1"]["admitted"], ad["A1"]["wrong_by_gold"], ad["A2"]["admitted"], ad["A2"]["wrong_by_gold"], pct(ad["A2"]["FALSE_ADMIT"]), pct(dev["GATE_COST"]), pct(dev["G6"]["false_abstain_rate"])))
for m in ms:
    pc = arms[m]["per_corpus"]
    md.append("Per corpus, M-%s: " % m + "; ".join("%s n=%d executed %d reading-correct %d A2 admitted %d wrong %d" % (c, d["n"], d["executed"], d["reading_correct"], d["A2_admitted"], d["A2_wrong"]) for c, d in pc.items()) + ".")
md.append("")
md.append("Three readings of the table. First, A1 versus A2: the engine's gates alone admit %s wrong by gold; adding agreement with the model's own answer removes %s of them. The own answer is the filter that works, even though it shares the reading's prior. Second, A0 versus A2 (A2 is a subset of A0): the honesty gates removed **%s** of A0's by-gold wrongs while costing %s of its admissions — on the three large models G-P6 and the structural rules bought nothing by gold on this corpus; they only earned their keep on haiku. Third, scale (H9): reading quality orders opus > fable > sonnet > haiku, and so does A1's wrong count; genuine counts are %s.\n"
          % (", ".join("%d (M-%s)" % (arms[m]["admission"]["A1"]["wrong_by_gold"], m) for m in ms),
             ", ".join("%d" % _own_removed(arms[m]) for m in ms),
             ", ".join("%d of %d (M-%s)" % (_gates_removed(arms[m]), arms[m]["admission"]["A0"]["wrong_by_gold"], m) for m in ms),
             ", ".join("%d%%" % round(100 * (1 - arms[m]["admission"]["A2"]["admitted"] / arms[m]["admission"]["A0"]["admitted"])) for m in ms),
             ", ".join("%d (M-%s)" % (len(genuine(arms[m])), m) for m in ms)))

md.append("## 3. Every by-gold wrong under A2, classified after the run (nothing relabelled)\n")
md.append("| arm | by gold | gold errata | gold format | rounding | unit conv. | convention | **GENUINE** | ids |")
md.append("|---|---|---|---|---|---|---|---|---|")
for m in ms:
    ids = arms[m]["admission"]["A2"]["wrong_ids"]
    cnt = {}
    for i in ids:
        cnt[CLASS.get(i, "unclassified")] = cnt.get(CLASS.get(i, "unclassified"), 0) + 1
    md.append("| M-%s | %d | %d | %d | %d | %d | %d | **%d** | %s |" % (m, len(ids), cnt.get("gold errata", 0), cnt.get("gold format", 0), cnt.get("rounding", 0), cnt.get("unit convention", 0), cnt.get("convention", 0), cnt.get("GENUINE", 0), ", ".join("%s (%s)" % (i, CLASS.get(i, "?")) for i in ids)))
md.append("")
md.append("Classes. *Gold errata*: the corpus answer does not follow from the text (a0375 7×7×6 vs gold 7×6; a1349 a perimeter formula that contradicts the stated figure; g0454 two people × 4/day × 30 = 240 vs gold 150). *Gold format*: the corpus answer is a fraction the grader parses as its numerator (\"5/2\", \"3/7\", \"1/6\"); the reading's value is the fraction. *Rounding*: means given exact where gold rounds to one decimal. *Unit convention*: cents vs dollars. *Convention*: a defensible reading the corpus does not share (does the father age during the 15 years; break-even year vs first earning year; \"another 1/4 of his land\" against the original vs the remainder; whether the host counts; whether \"the final day\" is a tenth day). *GENUINE*: the reading is wrong and the model's own answer shares the error — g1035 (sonnet: bottles every 3 ft on 24 ft, 8 gaps vs 7), g0790 (haiku: dropped the members-per-group factor), g0796 (fable: paid the final workforce once instead of three monthly payrolls). Full rows: `results/v19/M-<arm>_sealed_rows.json`; ledger `bug_audit_v1_9.md` notes V3–V7.\n")

md.append("## 4. What honesty costs, and what it buys\n")
md.append("G-P6 kills almost only correct readings (kills / of which correct: %s): on this corpus it is nearly a pure false-abstention gate, %s of executed readings. The four structural rules stay under the 3%% RULES bar each (S-RATIO is the largest at ~2.9%%). GATE-COST (G-P6 + rules) is %s, inside the 30%% bar. What it buys is in §2: on sonnet, opus and fable the gates removed no by-gold wrong that agreement would have admitted (fable: one); on haiku they removed 12 of 19. The engine-only rule A1 is worse than agreement-only A0 by gold on every arm. The safety in A2 comes from the own answer; the gates are a cost with a benefit only at the small scale.\n"
          % (", ".join("%d/%d" % (arms[m]["G6"]["kills"], arms[m]["G6"]["kills_of_correct"]) for m in ms),", ".join("%s (M-%s)" % (pct(arms[m]["G6"]["false_abstain_rate"]), m) for m in ms), ", ".join("%s (M-%s)" % (pct(arms[m]["GATE_COST"]), m) for m in ms)))

md.append("## 5. Reuse: measured, never served\n")
if reuse:
    md.append("A reading admitted under A2 was keyed by its cue signature (ask type, number count, roles18 cues) and, on pure keys only, bound positionally to every other SEALED item with the same key, gated and executed, then graded. " + "; ".join("M-%s: %d items had a candidate, %d were on impure keys and skipped, %d would have been served, **%d wrong**" % (m, reuse[m]["counts"]["items_with_candidate"], reuse[m]["counts"]["impure_key_skipped"], reuse[m]["REUSE_SERVED"], reuse[m]["REUSE_WRONG"]) for m in ORDER if m in reuse) + ". H6 and H7 both held: the cue key does not determine the reading (CUE-PURITY 8.3% on DEV), and \"pure\" is vacuous on singleton keys, so the pure library is mostly single-donor keys whose structure says nothing about the recipient. This is B32 on natural text: positional replay onto a look-alike question fires wrong. Nothing was served; the readings are one-phrasing reflexes.\n")
else:
    md.append("Not run.\n")

md.append("## 6. Bridge protocol and the record\n")
md.append("Every model ran as an agent with Read and Write only: 8 reading blocks and 6 answer blocks per arm, batch files only, no golds, no engine, no code. Files were written once and never overwritten; per-block null counts were reconciled against the agents' own reports. Fable's answer batches 00–11 did not land on disk from the first launch and were collected by a second launch of the same block before scoring (ledger V7). No local model was used. No API spend outside the bridge.\n")

md.append("## 7. Outcome on the frozen ladder\n")
if pri:
    a2 = pri["admission"]["A2"]
    g = genuine(pri)
    md.append("- GATE-CTRL: %s." % ("PASS" if (ctrl or {}).get("pass") else "FAIL"))
    md.append("- SAFETY-GEN (M-sonnet, A2, genuine wrong = 0): **%s** (%d: %s)." % ("fail" if g else "pass", len(g), ", ".join(g) or "—"))
    md.append("- SAFETY-FA ≤ 0.5%% by gold: %s (%s, %d of %d)." % ("pass" if a2["FALSE_ADMIT"] <= 0.005 else "fail", pct(a2["FALSE_ADMIT"]), a2["wrong_by_gold"], a2["admitted"]))
    md.append("- REACH ≥ 50%%: %s (%s)." % ("pass" if pri["REACH"] >= 0.50 else "fail", pct(pri["REACH"])))
    md.append("- GATE-COST ≤ 30%%: %s (%s)." % ("pass" if pri["GATE_COST"] <= 0.30 else "fail", pct(pri["GATE_COST"])))
    rl = dev["rules"] if dev else pri["rules"]
    md.append("- RULES < 3%% each on DEV: %s (%s)." % ("pass" if all(r["false_abstain_rate"] < 0.03 for r in rl.values()) else "fail", ", ".join("%s %s" % (k, pct(r["false_abstain_rate"])) for k, r in rl.items())))
    ru = reuse.get("sonnet")
    if ru:
        md.append("- REUSE-SAFE: fail (%d wrong of %d would-serve); reuse stays measured." % (ru["REUSE_WRONG"], ru["REUSE_SERVED"]))
    md.append("- SEALED-ONCE: every arm's readings, answers and score produced once.\n")
md.append("**OUTCOME %s.** %s\n" % (letter_, {
    "E": "One model, an honest engine and its own answer still admitted a genuine misread on the primary arm — one item (g1035, a fencepost count) in 863 admissions. The rule says one genuine is E, and the report says E. The aggregates around it: 0.12% genuine on sonnet, 0 on opus, 1 on fable, 1 on haiku; by-gold rates 0.9–1.4% of which the majority are corpus errata, fraction formatting and rounding conventions; reuse wrong-fires on every arm.",
    "D": "Safe and inert.", "C": "Safe in truth, wrong by the corpus.", "B": "Safe one-phrasing reflexes; reuse unsafe.", "A": "Reuse at zero wrong.", "F": "A control failed.", "?": "no sealed run"}[letter_]))

md.append("## 8. Hypotheses\n")
if pri:
    ad = pri["admission"]
    hs = [("H1 sonnet A2 genuine = 0", "FALSE (1: g1035)" if genuine(pri) else "TRUE"),
          ("H2 A2 FALSE-ADMIT ≤ 0.5%", "FALSE (%s)" % pct(ad["A2"]["FALSE_ADMIT"])),
          ("H3 A1 genuine > 0", "TRUE (A1 %d wrong by gold, ⊇ A2's genuine)" % ad["A1"]["wrong_by_gold"]),
          ("H4 A2 admits 60–80% of executed", "%s (%s)" % ("TRUE" if 0.6 <= ad["A2"]["share_of_executed"] <= 0.8 else "FALSE", pct(ad["A2"]["share_of_executed"]))),
          ("H5 each rule < 3% false abstention on DEV", "TRUE" if dev and all(r["false_abstain_rate"] < 0.03 for r in dev["rules"].values()) else "FALSE"),
          ("H6 CUE-PURITY < 70%", "TRUE (%s)" % pct(purity["CUE_PURITY"]) if purity else "—"),
          ("H7 reuse serves > 0 and wrong-fire ≠ 0", "TRUE (%d/%d)" % (reuse["sonnet"]["REUSE_WRONG"], reuse["sonnet"]["REUSE_SERVED"]) if "sonnet" in reuse else "—"),
          ("H8 REACH ≥ 50%", "TRUE (%s)" % pct(pri["REACH"])),
          ("H9 haiku genuine ≥ sonnet's, reach ≤", "TRUE (%d ≥ %d; %s ≤ %s)" % (len(genuine(arms["haiku"])), len(genuine(pri)), pct(arms["haiku"]["REACH"]), pct(pri["REACH"])) if "haiku" in arms else "—")]
    md.append("| hypothesis | result |")
    md.append("|---|---|")
    for h, r in hs:
        md.append("| %s | %s |" % (h, r))
    md.append("")

md.append("## 9. What V1.9 claims, and does not\n")
md.append("It claims the first gold-graded measurement of a one-model escalation-feedback loop on real questions across four model scales: reach, reading quality, and the by-gold and genuine false-admission rates under three admission rules, with every wrong published and classified. It claims that the model's own answer, not the engine's honesty gates, is what removes wrong readings at sonnet/opus/fable scale, and that the gates matter only at haiku scale. It claims that cue-keyed reuse of readings is unsafe on natural text and was never served. It does not claim SAFETY-GEN (one genuine wrong on the primary arm), does not claim the loop is safe to run live, and does not relabel the corpus golds it disagrees with.\n")
md.append("## Reproduction\n```\ngit checkout v1.9-final\npython tools/reader19v.py prep ; python tools/reader19v.py controls\n# bridge agents (Read/Write only) fill results/v19/bridge/readings19_<m>_sealed/ and answers19_<m>_sealed_NN.json\npython tools/reader19v.py score --phase dev --model sonnet\npython tools/reader19v.py score --phase sealed --model sonnet|opus|haiku|fable   # once each\npython tools/reader19v.py purity --model sonnet --phase dev\npython tools/reader19v.py reuse --model <m>\n```\n")
(REPO / "V1_9_FINAL_REPORT.md").write_text("\n".join(md), encoding="utf-8")

# ---------------------------------------------------------------- PDF
ss = getSampleStyleSheet()
TITLE = ParagraphStyle("t", parent=ss["Title"], fontSize=18, leading=23, spaceAfter=4, textColor=colors.HexColor("#023047"))
SUB = ParagraphStyle("sub", parent=ss["Normal"], fontSize=10.5, leading=14, textColor=colors.HexColor("#555555"), spaceAfter=10)
H = ParagraphStyle("H", parent=ss["Heading1"], fontSize=13, leading=16, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#023047"))
P = ParagraphStyle("P", parent=ss["Normal"], fontSize=9.3, leading=12.8, spaceAfter=6, alignment=4)
BUL = ParagraphStyle("B", parent=P, leftIndent=14, bulletIndent=4, spaceAfter=3, alignment=0)
CAP = ParagraphStyle("cap", parent=ss["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#666666"), spaceBefore=2, spaceAfter=10, alignment=1)
CODE = ParagraphStyle("code", parent=P, fontName="Courier", fontSize=7.2, leading=9.2, alignment=0, backColor=colors.HexColor("#f4f4f4"), borderPadding=5)


def esc(t):
    t = re.sub(r"&(?![a-zA-Z#][a-zA-Z0-9]*;)", "&amp;", t)
    t = t.replace("<", "&lt;").replace(">", "&gt;")
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)
    t = re.sub(r"`(.+?)`", stash, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\w)\*(.+?)\*(?!\w)", r"<i>\1</i>", t)
    for i2, c in enumerate(codes):
        t = t.replace("\x00%d\x00" % i2, "<font face='Courier' size='8'>%s</font>" % c)
    return t


def img(name, w=6.4):
    pth = CH / name
    if not pth.exists():
        return Spacer(1, 2)
    im = Image(str(pth))
    r = im.imageHeight / im.imageWidth
    im.drawWidth, im.drawHeight = w * inch, w * r * inch
    return im


def md_table(lines):
    rows = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(re.fullmatch(r"-+", c) for c in cells):
            continue
        rows.append([Paragraph(esc(c), ParagraphStyle("c", parent=P, fontSize=6.3, leading=7.8, alignment=0, spaceAfter=0)) for c in cells])
    t = Table(rows, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bbbbbb")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f1f5")), ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


FIGS = {"## 2.": ("v1_arms.png", "Fig. 1 — per arm: reach, reading quality, own-answer accuracy and A2 false admission by gold (dotted: 0.5% bar; labels: wrong/admitted and genuine count)."),
        "## 3.": ("v2_rules.png", "Fig. 2 — admitted and wrong-by-gold under the three admission rules, per arm."),
        "## 4.": ("v3_cost.png", "Fig. 3 — false abstention per gate, per arm."),
        "## 5.": ("v4_reuse.png", "Fig. 4 — cue-keyed reuse, measured and never served.")}
s = [Spacer(1, 36), Paragraph("The Adaptive Reflex Engine", TITLE), Paragraph("V1.9 — One-Model Reading Reflexes with Escalation Feedback", TITLE), Spacer(1, 6),
     Paragraph("Twenty-second experiment of the arc (after the S1 pre-study), on branch v1.9-reading. Pre-registered outcome %s. September 8, 2026. Spec frozen as v1.9-plan before any bridge call; sealed set hashed and scored once per arm." % letter_, SUB),
     HRFlowable(width="100%", color=colors.HexColor("#219ebc"), thickness=1.2), Spacer(1, 8)]
i, in_code, code_buf, tbl_buf = 0, False, [], []
while i < len(md):
    ln = md[i]
    if ln.startswith("```"):
        if in_code:
            s.append(Paragraph("<br/>".join(esc(x) for x in code_buf), CODE))
            code_buf = []
        in_code = not in_code
        i += 1
        continue
    if in_code:
        code_buf.append(ln)
        i += 1
        continue
    if ln.startswith("|"):
        tbl_buf.append(ln)
        if i + 1 >= len(md) or not md[i + 1].startswith("|"):
            s.append(md_table(tbl_buf))
            s.append(Spacer(1, 6))
            tbl_buf = []
        i += 1
        continue
    if ln.startswith("# "):
        i += 1
        continue
    if ln.startswith("## "):
        s.append(Paragraph(esc(ln[3:]), H))
        for key, (fn, cap) in FIGS.items():
            if ln.startswith(key):
                s.append(img(fn))
                s.append(Paragraph(cap, CAP))
    elif ln.startswith("- "):
        s.append(Paragraph("&bull; " + esc(ln[2:]), BUL))
    elif ln.strip():
        s.append(Paragraph(esc(ln), P))
    i += 1
SimpleDocTemplate(str(REPO / "V1_9_FINAL_REPORT.pdf"), pagesize=letter, leftMargin=0.8 * inch, rightMargin=0.8 * inch, topMargin=0.8 * inch, bottomMargin=0.8 * inch, title="V1.9 Final Report — One-Model Reading Reflexes", author="Kavan Shah").build(s)
print("OUTCOME", letter_, "arms", list(arms), "unclassified", {m: unclassified(v) for m, v in arms.items()})
