# -*- coding: utf-8 -*-
"""V1.10 final report (MD + PDF) from results/v110/<arm>_<split>_<tag>_summary.json.

Ladder and thresholds exactly as frozen in V110_SPEC.md sections 9-10.
Narrative paragraphs live in NARR below and are edited once, after the
sealed numbers exist; every number in the tables comes from the files.
"""
import json
import re
import sys
from collections import Counter
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
REPO = HERE.parent
OUT = REPO / "results" / "v110"
CH = HERE / "charts110"
CH.mkdir(exist_ok=True)
ORDER = ["sonnet", "opus", "haiku", "fable"]
TIERS = ["T1", "T2", "T3", "T3p", "T4", "P1", "P2", "P3", "P4", "PC", "D"]
TIER_NAME = {"T1": "one-step narrative", "T2": "2-3 step narrative", "T3": "GSM8K-train", "T3p": "SVAMP",
             "T4": "authored 4-6 step", "P1": "physics single formula", "P2": "physics chain k=3",
             "P3": "physics chain k=5-6", "P4": "authored physics story", "PC": "SciQ concept MC", "D": "distractor (no answer)"}
# which run tag is the version's number for each split
TAG = {"acq": "acq2", "dev": "dev", "seal": "seal", "replay": "replay"}
# post-hoc classes of every by-gold wrong under A2S / A2 on SEAL (nothing relabelled); filled after the sealed run
CLASS_FILE = json.loads((HERE.parent / "results" / "v110" / "class110.json").read_text(encoding="utf-8")) if (HERE.parent / "results" / "v110" / "class110.json").exists() else {"items": {}}


def cls(arm, split, iid):
    e = CLASS_FILE["items"].get("%s|%s|%s" % (arm, split, iid))
    return e["class"] if e else "unclassified"


def cls_why(arm, split, iid):
    e = CLASS_FILE["items"].get("%s|%s|%s" % (arm, split, iid))
    return e["why"] if e else ""


def load(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _merge(a, b):
    """Sum two summaries of disjoint tier sets (base = non-authored ACQ, acq2 = authored T4/P4; dev1 / dev2 likewise)."""
    if not a:
        return b
    if not b:
        return a
    m = json.loads(json.dumps(a))
    for t, c in b["by_tier"].items():
        if t in m["by_tier"]:
            for k, v in c.items():
                if isinstance(v, (int, float)):
                    m["by_tier"][t][k] = m["by_tier"][t].get(k, 0) + v
        else:
            m["by_tier"][t] = c
    for k, v in b["totals"].items():
        if isinstance(v, (int, float)):
            m["totals"][k] = m["totals"].get(k, 0) + v
    m["n"] = a.get("n", 0) + b.get("n", 0)
    m["library_T"], m["library_P"] = b.get("library_T", a.get("library_T")), b.get("library_P", a.get("library_P"))
    m["merged_from"] = [a.get("tag", "base"), b.get("tag", "acq2")]
    return m


# ACQ = base (non-authored, first pass) + acq2 (authored T4/P4, second pass); DEV = dev1 + dev2 likewise
PARTS = {"acq": ["base", "acq2"], "dev": ["dev1", "dev2"], "seal": ["seal"], "replay": ["replay"]}


def summ(arm, split, tag=None):
    if tag:
        return load(OUT / ("%s_%s_%s_summary.json" % (arm, split, tag)))
    if arm == "det":
        return load(OUT / ("det_%s_%s_summary.json" % (split, TAG[split])))
    out = None
    for t in PARTS[split]:
        s = load(OUT / ("%s_%s_%s_summary.json" % (arm, split, t)))
        if s:
            s["tag"] = t
            out = _merge(out, s)
    return out


def wrongs(arm, split, tag=None):
    tags = [tag] if tag else PARTS[split]
    out = []
    for t in tags:
        out += load(OUT / ("%s_%s_%s_wrong.json" % (arm, split, t))) or []
    return out


def pct(a, b):
    return "—" if not b else "%.1f%%" % (100.0 * a / b)


def g(c, k):
    return c.get(k, 0)


def genuine_ids(arm, split="seal"):
    return sorted({w["id"] for w in wrongs(arm, split) if w.get("rule") == "A2S" and cls(arm, split, w["id"]) == "GENUINE"})


def unclassified_ids(arm, split="seal"):
    return sorted({w["id"] for w in wrongs(arm, split) if w.get("rule") in ("A2S", "A2") and cls(arm, split, w["id"]) == "unclassified"})


# ---------------------------------------------------------------- collect
seal = {m: summ(m, "seal") for m in ORDER}
seal = {m: v for m, v in seal.items() if v}
replay = {m: summ(m, "replay") for m in ORDER}
replay = {m: v for m, v in replay.items() if v}
dev = {m: summ(m, "dev") for m in ORDER}
dev = {m: v for m, v in dev.items() if v}
acq = {m: summ(m, "acq") for m in ORDER}
acq = {m: v for m, v in acq.items() if v}
det = {sp: summ("det", sp) for sp in ("acq", "dev", "seal", "replay")}
det = {k: v for k, v in det.items() if v}
tok = load(OUT / "tokens110.json") or {}
ctrl = load(OUT / "controls110.json") or {}
rules = load(OUT / "rules110.json") or {}
manifest = load(OUT / "data" / "w400k_manifest.json") or {}
hashes = load(OUT / "data" / "HASHES.json") or {}
ledger = (REPO / "bug_audit_v1_10.md").read_text(encoding="utf-8") if (REPO / "bug_audit_v1_10.md").exists() else ""
BASE = {"sonnet": 64522, "opus": 58488, "haiku": 47005, "fable": 58748}  # empty-batch baselines (N3)


def tier_rows(s):
    return s["by_tier"] if s else {}


_ROWS = {}


def rows_for(arm, split):
    """Per-item rows of a sealed pass (cached)."""
    k = (arm, split)
    if k not in _ROWS:
        p = OUT / ("%s_%s_%s_rows.jsonl" % (arm, split, TAG[split]))
        _ROWS[k] = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []
    return _ROWS[k]


def _reach(arm, split, tiers, marginal=False):
    """SUGGEST-REACH = share of the E-SAMPLE items the exact path escalated that the suggestion served.
    Strict (the bar): suggest / (suggest + fresh + escalate) — every sampled item the exact path did not serve.
    Marginal (published beside it): suggest / (suggest + escalate) — items neither exact nor the fresh reading served.
    Un-sampled items have no model answer and escalate by construction (spec 5.3); they are excluded."""
    a = f = e = 0
    for r in rows_for(arm, split):
        if r.get("tier") not in tiers or not r.get("sampled"):
            continue
        pth = r.get("path", "").split(":")[0]
        if pth == "suggest":
            a += 1
        elif pth == "fresh":
            f += 1
        elif pth == "escalate":
            e += 1
    d = (a + e) if marginal else (a + f + e)
    return (a / d) if d else None


def reach_tier(s, t, split="seal", marginal=False):
    return _reach(s["arm"], split, (t,), marginal) if s else None


def reach_tier_all(s, t):
    c = s["by_tier"].get(t, {}) if s else {}
    a, e = g(c, "A2S_served"), g(c, "escalated")
    return (a / (a + e)) if (a + e) else None


def reach_s(s, split="seal", marginal=False):
    """REACH-S: SUGGEST-REACH pooled over T3 + T3p (strict, E-SAMPLE denominator)."""
    return _reach(s["arm"], split, ("T3", "T3p"), marginal) if s else None


def fa(s):
    """A2S wrong by gold / A2S served (all tiers)."""
    if not s:
        return None
    a, w = s["totals"]["A2S_served"], s["totals"]["A2S_WRONG"]
    return (w / a) if a else None


def chain_wrong(s):
    return sum(g(s["by_tier"].get(t, {}), "exact_WRONG") for t in ("P1", "P2", "P3")) if s else None


# ---------------------------------------------------------------- ladder
def ladder():
    pri = seal.get("sonnet")
    notes = []
    if not seal:
        return "?", ["no sealed run yet"]
    if not ctrl.get("pass"):
        return "F", ["GATE-CTRL fails"]
    gen = len(genuine_ids("sonnet")) if pri else None
    pc = any(v["totals"]["SAFETY_PC"] > 0 for v in seal.values())
    chain = any((chain_wrong(v) or 0) > 0 for v in list(seal.values()) + list(replay.values()) + [det[k] for k in ("seal", "replay") if k in det])
    if pri and gen:
        notes.append("SAFETY-GEN fails: %d genuine A2S wrongs on M-sonnet SEAL" % gen)
    if pc:
        notes.append("SAFETY-PC fails")
    if chain:
        notes.append("SAFETY-CHAIN fails (P1-P3 model-free wrong on a sealed pass: %s)" % ", ".join(
            "%s/%s=%d" % (n, sp, chain_wrong(v)) for n, sp, v in [(m, "seal", v) for m, v in seal.items()] + [(m, "replay", v) for m, v in replay.items()] + [("det", k, det[k]) for k in ("seal", "replay") if k in det] if (chain_wrong(v) or 0) > 0))
    rules_bad = [m for m, r in rules.items() if not (r["Z-SLOT"]["pass_3pct"] and r["S-MULTI"]["pass_3pct"])]
    if rules_bad:
        notes.append("RULES > 3%% false abstention on %s (reported; no ladder letter assigned by the spec)" % ", ".join(rules_bad))
        notes = [n for n in notes]  # keep
    if [n for n in notes if not n.startswith("RULES")]:
        return "E", notes
    low = [m for m, v in seal.items() if (reach_s(v) or 0) < 0.30]
    if low:
        return "D", ["REACH-S < 30%% on %s" % ", ".join(low)]
    fa_bad = [m for m, v in seal.items() if (fa(v) or 0) > 0.010]
    tok_bad = tokens_ratio() is not None and tokens_ratio() > 0.50
    if fa_bad or tok_bad:
        n = []
        if fa_bad:
            n.append("SAFETY-FA > 1.0%% on %s" % ", ".join(fa_bad))
        if tok_bad:
            n.append("TOKENS > 50%")
        return "C", n
    kc_ok = all(v["totals"]["KC_served"] > 0 and v["totals"]["KC_WRONG"] == 0 for v in seal.values())
    return ("A" if kc_ok else "B"), ["KC-SAFE %s" % ("holds" if kc_ok else "not met")]


def tokens_ratio():
    """engine-in-front TOKENS/QUERY over LLM-only, extrapolated by escalation rate on SEAL (sonnet arm); None until measurable."""
    if "sonnet" not in seal or not tok:
        return None
    ans = tok.get("sonnet|answer|seal") or tok.get("sonnet|answer|acq")
    if not ans or not ans.get("items"):
        return None
    esc_rate = seal["sonnet"]["totals"]["escalated"] / max(1, seal["sonnet"]["totals"]["n"])
    return esc_rate  # marginal tokens are the same per escalated query: ratio = escalation share


# ---------------------------------------------------------------- figures
def fig_arms():
    if not seal:
        return
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.6))
    ms = list(seal)
    x = range(len(ms))
    ax[0].bar(x, [100 * (reach_s(seal[m]) or 0) for m in ms], color="#219ebc")
    ax[0].axhline(30, ls=":", color="k"); ax[0].set_title("SUGGEST-REACH on T3+T3' (SEAL)"); ax[0].set_ylabel("%")
    ax[1].bar(x, [100 * (fa(seal[m]) or 0) for m in ms], color="#fb8500")
    ax[1].axhline(1.0, ls=":", color="k"); ax[1].set_title("A2S wrong by gold / served"); ax[1].set_ylabel("%")
    ax[2].bar(x, [len(genuine_ids(m)) for m in ms], color="#d62828")
    ax[2].set_title("GENUINE wrongs under A2S (SEAL)")
    for a in ax:
        a.set_xticks(list(x)); a.set_xticklabels(ms)
    fig.tight_layout(); fig.savefig(CH / "f1_arms.png", dpi=150); plt.close(fig)


def fig_tiers():
    if not seal:
        return
    fig, ax = plt.subplots(figsize=(12, 3.8))
    w = 0.8 / max(1, len(seal))
    for i, (m, s) in enumerate(seal.items()):
        ys = []
        for t in TIERS:
            c = s["by_tier"].get(t, {})
            n = g(c, "n") - g(c, "excluded_author")
            served = g(c, "exact_served") + g(c, "A2S_served") + max(0, g(c, "A2_admitted") - g(c, "plan_agree") - g(c, "plan_disagree"))
            ys.append(100 * served / n if n else 0)
        ax.bar([j + i * w for j in range(len(TIERS))], ys, width=w, label=m)
    ax.set_xticks([j + 0.4 - w / 2 for j in range(len(TIERS))]); ax.set_xticklabels(TIERS)
    ax.set_ylabel("% items served by any engine path"); ax.set_title("Served share per tier, SEAL (exact + suggested + fresh)"); ax.legend()
    fig.tight_layout(); fig.savefig(CH / "f2_tiers.png", dpi=150); plt.close(fig)


def fig_curve():
    if not acq:
        return
    fig, ax = plt.subplots(figsize=(8, 3.4))
    for m, s in acq.items():
        cv = s.get("curve") or []
        if cv:
            ax.plot([c["n"] for c in cv], [c["A2S_served"] for c in cv], marker="o", label="%s A2S served" % m)
    ax.set_xlabel("ACQ items processed"); ax.set_ylabel("cumulative A2S serves"); ax.set_title("Acquisition curve (checkpoints every 20k)"); ax.legend()
    fig.tight_layout(); fig.savefig(CH / "f3_curve.png", dpi=150); plt.close(fig)


def fig_tokens():
    if not tok:
        return
    fig, ax = plt.subplots(figsize=(8, 3.4))
    keys = sorted(k for k in tok if tok[k].get("tokens_per_item"))
    ax.barh(keys, [tok[k]["tokens_per_item"] for k in keys], color="#8ecae6")
    ax.set_xlabel("harness tokens per item (raw, incl. fixed agent overhead)"); ax.set_title("Bridge usage by model | role | split")
    fig.tight_layout(); fig.savefig(CH / "f4_tokens.png", dpi=150); plt.close(fig)


# ---------------------------------------------------------------- markdown
NARR = load(HERE / "report110_narrative.json") or {}


def N(key, default=""):
    return NARR.get(key, default)


def arm_tier_table(s, split_name):
    L = ["| tier | n | exact served / wrong | A2S served / wrong | A0S served / wrong | KC served / wrong | fresh A2 / wrong | escalated | own correct | reach (A2S of non-exact) |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for t in TIERS:
        c = s["by_tier"].get(t)
        if not c:
            continue
        n = g(c, "n") - g(c, "excluded_author")
        L.append("| %s | %s | %d / %d | %d / %d | %d / %d | %d / %d | %d / %d | %d | %s | %s |" % (
            t, ("%d" % n) + (" (+%d author-excluded)" % g(c, "excluded_author") if g(c, "excluded_author") else ""),
            g(c, "exact_served"), g(c, "exact_WRONG"), g(c, "A2S_served"), g(c, "A2S_WRONG"), g(c, "A0S_served"), g(c, "A0S_WRONG"),
            g(c, "KC_served"), g(c, "KC_WRONG"), g(c, "A2_admitted"), g(c, "A2_WRONG"), g(c, "escalated"),
            pct(g(c, "own_correct"), g(c, "own_answered")), pct(g(c, "A2S_served"), g(c, "A2S_served") + g(c, "escalated"))))
    T = s["totals"]
    L.append("| **all** | %d | %d / %d | %d / %d | %d / %d | %d / %d | %d / %d | %d | %s | — |" % (
        T["n"] - T["excluded_author"], T["exact_served"], T["exact_WRONG"], T["A2S_served"], T["A2S_WRONG"], T["A0S_served"], T["A0S_WRONG"],
        T["KC_served"], T["KC_WRONG"], T["A2_admitted"], T["A2_WRONG"], T["escalated"], pct(T["own_correct"], T["own_answered"])))
    return L


def build_md():
    letter_, notes = ladder()
    md = []
    md.append("# V1.10 Final Report — Suggest, Don't Serve")
    md.append("")
    md.append("Branch v1.10-suggest; spec frozen as v1.10-plan before any bridge call; W-400K hashed before any run; SEAL and REPLAY scored once per arm. **Pre-registered outcome: %s** (%s)." % (letter_, "; ".join(notes)))
    md.append("")
    md.append("## Headline")
    md.append(N("headline", "_(narrative to be written after the sealed run)_"))
    md.append("")
    md.append("## 1. What was run")
    mf = manifest
    md.append("- W-400K: %s items (tier quotas in the spec; N4 in the ledger). Splits acq %s / dev %s / seal %s / replay %s by sha1(id)." % (
        mf.get("n", "?"), mf.get("by_split", {}).get("acq", "?"), mf.get("by_split", {}).get("dev", "?"), mf.get("by_split", {}).get("seal", "?"), mf.get("by_split", {}).get("replay", "?")))
    md.append("- Arms: M-sonnet, M-opus, M-haiku, M-fable (one model per arm for answers, readings and authoring QC) and D (deterministic engine only). Engine identical across arms.")
    md.append("- Bridge: Read/Write-only agents on batch files without golds; harness-reported usage logged per agent (never self-report).")
    md.append(N("what_was_run", ""))
    md.append("")
    md.append("## 2. Results per arm on SEAL (run once)")
    for m, s in seal.items():
        md.append("### M-%s — SEAL n=%d, sampled %d, %.2f ms/query" % (m, s["n"], s["sampled"], s["ms_per_query"]))
        md += arm_tier_table(s, "seal")
        md.append("")
    if "seal" in det:
        s = det["seal"]
        md.append("### D (engine only) — SEAL n=%d" % s["n"])
        md += arm_tier_table(s, "seal")
        md.append("")
    md.append(N("results", ""))
    md.append("")
    md.append("## 3. Every by-gold wrong on SEAL, classified after the run (nothing relabelled)")
    md.append("| arm | rule | id | tier | value | gold | class |")
    md.append("|---|---|---|---|---|---|---|")
    for m in seal:
        for w in wrongs(m, "seal"):
            md.append("| %s | %s | %s | %s | %s | %s | %s |" % (m, w.get("rule", w.get("path", "exact")), w["id"], w.get("tier", ""), w.get("value"), w.get("gold"), cls(m, "seal", w["id"])))
    md.append("")
    md.append(N("wrongs", ""))
    md.append("")
    md.append("## 4. Reach: what the suggestion serves that the fresh reading could not")
    md.append("| arm | REACH-S (T3+T3', bar 30%) | T1 | T2 | T4 | P4 | A2S wrong / served | A0S wrong / served |")
    md.append("|---|---|---|---|---|---|---|---|")
    for m, s in seal.items():
        md.append("| %s | %s | %s | %s | %s | %s | %d / %d | %d / %d |" % (
            m, "—" if reach_s(s) is None else "%.1f%%" % (100 * reach_s(s)),
            *["—" if reach_tier(s, t) is None else "%.1f%%" % (100 * reach_tier(s, t)) for t in ("T1", "T2", "T4", "P4")],
            s["totals"]["A2S_WRONG"], s["totals"]["A2S_served"], s["totals"]["A0S_WRONG"], s["totals"]["A0S_served"]))
    md.append("")
    md.append(N("reach", ""))
    md.append("")
    md.append("## 5. Physics: chains model-free, stories by reading")
    md.append("| arm | P1 served / wrong | P2 served / wrong | P3 served / wrong | P4 A2S / wrong | P4 fresh A2 / wrong | PC certified |")
    md.append("|---|---|---|---|---|---|---|")
    for m, s in list(seal.items()) + ([("D", det["seal"])] if "seal" in det else []):
        b = s["by_tier"]
        md.append("| %s | %d / %d | %d / %d | %d / %d | %d / %d | %d / %d | %d |" % (
            m, g(b.get("P1", {}), "exact_served"), g(b.get("P1", {}), "exact_WRONG"), g(b.get("P2", {}), "exact_served"), g(b.get("P2", {}), "exact_WRONG"),
            g(b.get("P3", {}), "exact_served"), g(b.get("P3", {}), "exact_WRONG"), g(b.get("P4", {}), "A2S_served"), g(b.get("P4", {}), "A2S_WRONG"),
            g(b.get("P4", {}), "A2_admitted"), g(b.get("P4", {}), "A2_WRONG"), s["totals"]["SAFETY_PC"]))
    md.append("")
    md.append(N("physics", ""))
    md.append("")
    md.append("## 6. Tokens (harness-reported, marginal over the empty-batch baseline)")
    md.append("| model | role | split | agents | items | raw tokens/item | marginal tokens/item |")
    md.append("|---|---|---|---|---|---|---|")
    for k in sorted(tok):
        v = tok[k]
        m, role, sp = k.split("|")
        marg = (v["tokens"] - v["agents"] * BASE.get(m, 0)) / v["items"] if v["items"] else None
        md.append("| %s | %s | %s | %d | %d | %s | %s |" % (m, role, sp, v["agents"], v["items"], v["tokens_per_item"], "—" if marg is None else "%.0f" % marg))
    md.append("")
    md.append(N("tokens", ""))
    md.append("")
    md.append("## 7. DEV: rules and their cost")
    for m, s in dev.items():
        md.append("### M-%s — DEV n=%d" % (m, s["n"]))
        md += arm_tier_table(s, "dev")
        md.append("")
    if rules:
        md.append("")
        md.append("RULES on DEV (false abstention of a rule = sampled DEV T-tier items the rule blocked on which the un-blocked suggestion would have served the gold, over all sampled items; bar < 3%):")
        md.append("")
        md.append("| arm | sampled | Z-SLOT blocked | Z-SLOT false abst. | S-MULTI blocked | S-MULTI would serve (correct/wrong) | S-MULTI false abst. |")
        md.append("|---|---|---|---|---|---|---|")
        for m, r in rules.items():
            md.append("| %s | %d | %d | %s | %d | %d (%d/%d) | %s |" % (m, r["sampled"], r["Z-SLOT"]["blocked"], pct(r["Z-SLOT"]["would_serve_correct"], r["sampled"]),
                      r["S-MULTI"]["blocked"], r["S-MULTI"]["would_serve"], r["S-MULTI"]["would_serve_correct"], r["S-MULTI"]["would_serve_wrong"], pct(r["S-MULTI"]["would_serve_correct"], r["sampled"])))
        md.append("")
    md.append(N("dev", ""))
    md.append("")
    md.append("## 8. Acquisition and REPLAY")
    for m, s in acq.items():
        md.append("- M-%s ACQ: library T=%d P=%d probated=%d; A2S served %d / wrong %d; curve %s" % (
            m, s["library_T"], s["library_P"], s["probated_T"], s["totals"]["A2S_served"], s["totals"]["A2S_WRONG"],
            ", ".join("%dk:%d" % (c["n"] // 1000, c["A2S_served"]) for c in s.get("curve", []))))
    if replay:
        md.append("")
        md.append("Every by-gold wrong on REPLAY (classified after the run):")
        md.append("")
        md.append("| arm | rule | id | tier | value | gold | class |")
        md.append("|---|---|---|---|---|---|---|")
        for m in replay:
            for w in wrongs(m, "replay"):
                md.append("| %s | %s | %s | %s | %s | %s | %s |" % (m, w.get("rule", w.get("exact_reason", "exact")), w["id"], w.get("tier", ""), w.get("value"), w.get("gold"), cls(m, "replay", w["id"])))
        md.append("")
    for m, s in replay.items():
        md.append("- M-%s REPLAY: A2S served %d / wrong %d; exact %d / wrong %d; escalated %d of %d" % (
            m, s["totals"]["A2S_served"], s["totals"]["A2S_WRONG"], s["totals"]["exact_served"], s["totals"]["exact_WRONG"], s["totals"]["escalated"], s["totals"]["n"]))
    md.append("")
    md.append(N("acq", ""))
    md.append("")
    md.append("## 9. Controls")
    md.append("| control | result |")
    md.append("|---|---|")
    for k, v in ctrl.items():
        md.append("| %s | %s |" % (k, v))
    md.append("")
    md.append("## 10. Hypotheses")
    md.append(N("hypotheses", "_(H1–H12 verdicts after the sealed run)_"))
    md.append("")
    md.append("## 11. Outcome on the frozen ladder")
    md.append("Outcome **%s**: %s" % (letter_, "; ".join(notes)))
    md.append(N("ladder", ""))
    md.append("")
    md.append("## 12. What V1.10 claims, and does not")
    md.append(N("claims", ""))
    md.append("")
    md.append("## 13. Ledger (bug_audit_v1_10.md)")
    for ln in ledger.splitlines():
        if ln.startswith("## "):
            md.append("- " + ln[3:])
    md.append("")
    md.append("## Reproduction")
    md.append("```")
    md.append("python tools/build_w400k.py                      # W-400K + HASHES.json (already built; hashes must match)")
    md.append("python tools/engine110.py controls               # controls110.json pass=true")
    md.append("python tools/engine110.py run --arm <arm> --split seal --tag seal --lib-in results/v110/lib_<arm>_acq2.json")
    md.append("python tools/engine110.py tokens                 # tokens110.json from bridge/usage.jsonl")
    md.append("python tools/report110.py                        # this report")
    md.append("```")
    return md


# ---------------------------------------------------------------- PDF
ss = getSampleStyleSheet()
TITLE = ParagraphStyle("t", parent=ss["Title"], fontSize=18, leading=23, spaceAfter=4, textColor=colors.HexColor("#023047"))
SUB = ParagraphStyle("sub", parent=ss["Normal"], fontSize=10.5, leading=14, textColor=colors.HexColor("#555555"), spaceAfter=10)
H = ParagraphStyle("H", parent=ss["Heading1"], fontSize=13, leading=16, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#023047"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=10.5, leading=13, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#023047"))
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
        rows.append([Paragraph(esc(c), ParagraphStyle("c", parent=P, fontSize=6.0, leading=7.4, alignment=0, spaceAfter=0)) for c in cells])
    t = Table(rows, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bbbbbb")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f1f5")), ("TOPPADDING", (0, 0), (-1, -1), 1.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


FIGS = {"## 2.": ("f1_arms.png", "Fig. 1 — per arm on SEAL: suggest-reach on the real tiers (dotted: 30% bar), A2S false admission by gold (dotted: 1.0% bar), genuine wrongs."),
        "## 4.": ("f2_tiers.png", "Fig. 2 — share of SEAL items served by any engine path, per tier and arm."),
        "## 6.": ("f4_tokens.png", "Fig. 3 — raw harness tokens per item by model, role and split (fixed agent overhead included; the marginal figure is in the table)."),
        "## 8.": ("f3_curve.png", "Fig. 4 — acquisition curve: cumulative suggested serves against ACQ position.")}


def build_pdf(md, letter_):
    s = [Spacer(1, 36), Paragraph("The Adaptive Reflex Engine", TITLE), Paragraph("V1.10 — Suggest, Don't Serve", TITLE), Spacer(1, 6),
         Paragraph("Twenty-third experiment of the arc, on branch v1.10-suggest. Pre-registered outcome %s. September 2026. Spec frozen as v1.10-plan before any bridge call; W-400K hashed before any run; SEAL and REPLAY scored once per arm." % letter_, SUB),
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
        if ln.startswith("### "):
            s.append(Paragraph(esc(ln[4:]), H2))
        elif ln.startswith("## "):
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
    SimpleDocTemplate(str(REPO / "V1_10_FINAL_REPORT.pdf"), pagesize=letter, leftMargin=0.8 * inch, rightMargin=0.8 * inch, topMargin=0.8 * inch, bottomMargin=0.8 * inch,
                      title="V1.10 Final Report — Suggest, Don't Serve", author="Kavan Shah").build(s)


if __name__ == "__main__":
    fig_arms(); fig_tiers(); fig_curve(); fig_tokens()
    md = build_md()
    letter_, notes = ladder()
    (REPO / "V1_10_FINAL_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    build_pdf(md, letter_)
    print("OUTCOME", letter_, notes, "arms(seal)", list(seal), "unclassified", {m: unclassified_ids(m) for m in seal})
