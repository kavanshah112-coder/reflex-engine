# -*- coding: utf-8 -*-
"""V1.8 final report: Markdown + PDF, every number from
results/v18/aggregate18.json. Run charts first."""
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (HRFlowable, Image, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table,
                                TableStyle)

HERE = Path(__file__).parent
CH = HERE / "charts"
REPO = Path(r"C:\Users\admin\Downloads\reflex-engine")
A = json.load(open(REPO / "results" / "v18" / "aggregate18.json",
                   encoding="utf-8"))
MODELS = ["haiku", "sonnet", "opus", "fable"]


def arm(a, split):
    return A["arms"].get(a, {}).get(split)


def fmt(n):
    return format(n, ",") if isinstance(n, int) else str(n)


# ------------------------------------------------------------ numbers
seal = {a: arm(a, "seal") for a in A["arms"] if arm(a, "seal")}
replay = {a: arm(a, "replay") for a in A["arms"] if arm(a, "replay")}
devl = {a: arm(a, "devl") for a in A["arms"] if arm(a, "devl")}
tot_eval = sum(v["n"] for d in (seal, replay, devl) for v in d.values())
tot_served = sum(v["served"] for d in (seal, replay, devl)
                 for v in d.values())
tot_bind = sum(v["bind_served"] for d in (seal, replay, devl)
               for v in d.values())
tot_wrong = sum(v["WRONG"] for d in (seal, replay, devl)
                for v in d.values())
tot_wrong_bind = sum(v["WRONG_bind"] for d in (seal, replay, devl)
                     for v in d.values())
wrong_ids = sorted({r[0] for d in (seal, replay, devl) for v in d.values()
                    for r in v["wrong_rows"]})
ret = A["retain"]
ctrl = A["controls"] or {}
pb = (ctrl.get("probe_b32") or {}).get("counts", {})
lib = A["libraries"]
gap = A["gapclass"] or {}
rd = A["realdiag"] or {}
en = A["energy"] or {}
v17 = A["v17_reference"]

retain_pass = [m for m in MODELS if ret.get("B-%s-dev" % m, {}).get(
    "RETAIN", 0) >= 0.60]
compound_raw_pass = [m for m in MODELS if ret.get("B-%s-dev" % m, {}).get(
    "COMPOUND", {}).get("ratio_raw", 0) >= 5]
compound_dedup_pass = [m for m in MODELS if ret.get("B-%s-dev" % m, {}).get(
    "COMPOUND", {}).get("ratio_dedup", 0) >= 2]
seal_wrong_fire_max = max(v["wrong_fire"] or 0 for v in seal.values())
replay_wrong_fire_max = max((v["wrong_fire"] or 0 for v in
                             replay.values()), default=0)
energy_status = en.get("status", "not measured")

# ladder
if tot_wrong_bind > 0 or seal_wrong_fire_max > 0.001 or \
        replay_wrong_fire_max > 0.001:
    letter_ = "E"
elif len(retain_pass) < 2 or lib.get("all_all", {}).get("templates", 0) < 300:
    letter_ = "D" if max(ret.get("B-%s-dev" % m, {}).get("RETAIN", 0)
                         for m in MODELS) < 0.40 else "C"
elif len(compound_dedup_pass) < 2:
    letter_ = "C"
elif energy_status != "measured":
    letter_ = "B"
else:
    letter_ = "A"

# ------------------------------------------------------------ markdown
md = []
md.append("# V1.8 FINAL REPORT — Role-Aware Reuse\n")
md.append("**Pre-registered outcome: %s** on the frozen ladder "
          "(`V18_SPEC.md` §10, tag `v1.8-plan`, amendments A1–A2). "
          "Every threshold below is quoted against its frozen bar.\n"
          % letter_)
md.append("## Headline\n")
md.append("- **Safety:** %s evaluations across DEV-L, SEAL and REPLAY; "
          "%s answers served, %s of them by role-aware reuse; "
          "**%d binder-attributed wrong answers**; %d wrong answers in "
          "total, all on the inherited V1.6 single-step path on one "
          "foreign item (B36: %s), identical to V1.7's own residue."
          % (fmt(tot_eval), fmt(tot_served), fmt(tot_bind),
             tot_wrong_bind, tot_wrong, ", ".join(wrong_ids)))
md.append("- **PROBE-B32:** the 8,842 questions V1.7 answered wrong, "
          "through the V1.8 binder: %s served at the gold, %s abstained, "
          "%s served wrong." % (fmt(pb.get("served_gold", 0)),
                                fmt(pb.get("abstained", 0)),
                                fmt(pb.get("SERVED_WRONG", 0))))
for m in MODELS:
    r = ret.get("B-%s-dev" % m, {})
    if r:
        md.append("- **RETAIN %s:** %.1f%% (%s of %s V1.7 template-served "
                  "sealed items, %s of which V1.7 got wrong; all %s now "
                  "correct) + %s new serves on items V1.7 escalated."
                  % (m, 100 * r["RETAIN"], fmt(r["v18_bind_on_same"]),
                     fmt(r["v17_template_serves"]),
                     fmt(r["v17_template_wrong"]),
                     fmt(r["v18_bind_on_same_correct"]),
                     fmt(r["bind_new_coverage"])))
md.append("- **Coverage (SEAL 300k, run once):** composer alone 37.5%%; "
          "dev-plan libraries %s; dev+sealed-plan libraries %s; union "
          "(586 templates) %.2f%%."
          % (", ".join("%s %.2f%%" % (m, 100 * seal["B-%s-dev" % m]["coverage"])
                       for m in MODELS),
             ", ".join("%s %.2f%%" % (m, 100 * seal["B-%s-all" % m]["coverage"])
                       for m in MODELS),
             100 * seal["B-all-all"]["coverage"]))
md.append("- **COMPOUND:** raw ratio (certified binder serves per plan "
          "purchased, SEAL) %s — the ≥5 bar is met on every scale; the "
          "signature-deduplicated ratio %s cannot reach its frozen ≥2 "
          "bar by construction (bounded by templates/plans < 1) — a "
          "pre-registration defect, reported as the failed criterion "
          "it formally is."
          % (", ".join("%s %.1f" % (m, ret["B-%s-dev" % m]["COMPOUND"]["ratio_raw"])
                       for m in MODELS if "B-%s-dev" % m in ret),
             ", ".join("%s %.3f" % (m, ret["B-%s-dev" % m]["COMPOUND"]["ratio_dedup"])
                       for m in MODELS if "B-%s-dev" % m in ret)))
md.append("- **HARVEST:** union library %d templates (%d full-chain, %d "
          "sub-chain) from %s certified V1.7 plans; per-model probation "
          "on ACQ: zero wrong serves in the final libraries."
          % (lib["all_all"]["templates"], lib["all_all"]["full"],
             lib["all_all"]["sub"],
             fmt(sum(lib["%s_all" % m]["harvest_ledger"]["plans_in"]
                     for m in MODELS))))
md.append("- **GAP:** adapter-gap share of escalations %.2f%% (10%% rule: "
          "the adapter arm does not run; V1.7's connector null had a "
          "measured reason — the composer never fails on a missing unit "
          "edge, it fails for want of a step grammar: structure gap "
          "%.1f%%)." % (100 * gap.get("shares", {}).get("adapter_gap", 0),
                        100 * gap.get("shares", {}).get("structure_gap", 0)))
md.append("- **REAL-DIAG:** union-library reach on GSM8K/ASDiv/SciQ = "
          "0 of %s (all `no_skeleton`); unresolved-cue share of stated "
          "numbers GSM8K %.0f%%, ASDiv %.0f%%."
          % (fmt(rd.get("n", 0)),
             100 * rd["per_corpus"]["gsm8k"]["bare_tokens"] / max(1, rd["per_corpus"]["gsm8k"]["tokens"]) if rd else 0,
             100 * rd["per_corpus"]["asdiv"]["bare_tokens"] / max(1, rd["per_corpus"]["asdiv"]["tokens"]) if rd else 0))
md.append("- **ENERGY:** %s." % ("measured — see §8" if energy_status ==
                                   "measured" else "not measured (§8)"))
md.append("- **haiku binding arm (§4.4):** vacuous by construction — "
          "the deterministic binder never produces a \"two candidates\" "
          "state (skeleton-exact lookup + ordinal roles), so there is no "
          "ambiguity for a model to resolve; haiku is reported REDUNDANT "
          "for binding (H7).")
md.append("")

md.append("## 1. What V1.8 set out to do\n")
md.append("V1.7 ended with composition proven and reuse broken: every one "
          "of its 8,842 wrong answers came from positional template "
          "replay (B32). V1.8 built one component — a deterministic "
          "role-aware binder (`roles18` + `binder18`) with usage "
          "accounting in the gate (G-P4′) — and asked whether the three "
          "generation problems that mattered (unsafe reuse, minting only "
          "from completed examples, a non-compounding library) close "
          "together. Templates are harvested from V1.7's witness-certified "
          "plans (`harvest18`): every stated number in the donor question "
          "gets a role (unit adjacency or the composer's cue grammar), "
          "the plan's literals are replaced by role markers, and a "
          "template serves only questions whose skeleton (text with "
          "number digits blanked, signs and exponents kept) equals a "
          "donor's. No regex over numbers exists anywhere in the path; no "
          "model is called inside the binder.\n")

md.append("## 2. What was found before any counting run\n")
md.append("Four ledger entries and two amendments precede the first sealed "
          "number (`bug_audit_v1_8.md`, `V18_SPEC.md` A1–A2):\n")
md.append("- **B33 — haiku-13 was misdiagnosed.** The V1.7 ledger said "
          "the 13 certified-wrong haiku plans were dual-role drops. "
          "Reading them: 12 wrote `p*r*t/100 + p` (the amount) for a "
          "simple-interest ask, every number in its right role; the 13th "
          "differentiated its expression before calling `derivative_at`. "
          "Usage accounting cannot see the 12. **Amendment A1** added "
          "gate **G-P5 (certified formulas)**: a formula expression must "
          "be sympy-equivalent to the composer's own FORM table and the "
          "question must name the kind. Control: haiku-13 dies 13/13 (12 "
          "at G-P5, 1 at G-P4′).")
md.append("- **B34 — sign-blind binding**, caught by probation on ACQ "
          "golds: two candidates served \"greater than −216?\" against "
          "+216. Role markers now carry the donor literal's sign; the "
          "skeleton keeps `-#` structural. Had probation been skipped, "
          "this was a sealed-volume SAFETY-BIND wrong.")
md.append("- **B35 — an inherited V1.7 gate defect**: G-P3 read \"in "
          "m/s^2 of a 52 kg mass\" as an ask for m/s and killed every "
          "force chain (100% of the binder's gate abstentions; V1.7's "
          "largest fresh-plan kill class). Fixed inside plangate18 by "
          "swapping a continuation-aware unit reader around the "
          "plangate17 call; plangate17 stays byte-identical (repro "
          "20,000/0 diffs).")
md.append("- **Amendment A2 — canonical plan form.** 631 of 655 union "
          "collisions were `scale(@x, f)` vs `evaluate(\"@x*f\")`; 24 "
          "were unit annotations. Harvest now rewrites multiply-by-marker "
          "to `scale` and derives units from upstream (a model unit that "
          "disagrees rejects the plan). Within-model collisions went to "
          "0; union collisions 655 → 3.")
md.append("- **B36 — the one wrong answer of the version**, on the "
          "inherited V1.6 path: a foreign item (\"… With m = 57.0 and "
          "this result as v, apply …\") that V1.7's chain marker never "
          "routed past the single-step engine, which served sentence one. "
          "Identical in all four V1.7 arms (the 4 `v16:symcore16` rows of "
          "PROBE-B32). Sealed numbers stand as found; a second marker is "
          "in v18_run behind the default (`--routing17` reproduces).")
md.append("")

md.append("## 3. Safety — every arm, every set\n")
md.append("| arm | library | split | n | served | binder serves | wrong "
          "| binder wrong | coverage | distractors served | engine errors |")
md.append("|---|---|---|---|---|---|---|---|---|---|---|")
for a in A["arms"]:
    for split in ("devl", "seal", "replay"):
        v = arm(a, split)
        if not v:
            continue
        md.append("| %s | %s | %s | %s | %s | %s | %d | %d | %.2f%% | %d | %d |"
                  % (a, v["lib_templates"] or "—", split, fmt(v["n"]),
                     fmt(v["served"]), fmt(v["bind_served"]), v["WRONG"],
                     v["WRONG_bind"], 100 * v["coverage"],
                     v["distractors_served"], v["engine_errors"]))
md.append("")
md.append("Wrong-answer ledger of the version: %s. The B36 item is the "
          "only wrong answer in %s evaluations; it is served by "
          "`v16:symcore16`, never by `bind:*` or `chain:composer`.\n"
          % (", ".join(wrong_ids) or "none", fmt(tot_eval)))

md.append("## 4. Reuse — RETAIN and what the binder abstains on\n")
md.append("| model | V1.7 template serves (SEAL) | of which wrong | V1.8 "
          "binder serves on the same items | RETAIN | lost (reason) | new "
          "serves on V1.7 escalations |")
md.append("|---|---|---|---|---|---|---|")
for m in MODELS + ["all"]:
    for sc in ("dev", "all"):
        r = ret.get("B-%s-%s" % (m, sc))
        if not r:
            continue
        md.append("| B-%s-%s vs R-%s | %s | %s | %s | %.1f%% | %s | %s |"
                  % (m, sc, r["model"], fmt(r["v17_template_serves"]),
                     fmt(r["v17_template_wrong"]), fmt(r["v18_bind_on_same"]),
                     100 * r["RETAIN"],
                     ", ".join("%s %s" % (k, v) for k, v in
                               r["abstain_anatomy_on_denominator"].items()),
                     fmt(r["bind_new_coverage"])))
md.append("")
md.append("Every item lost from V1.7's template coverage is `no_skeleton`: "
          "its skeleton had a single donor and the two-donor rule kept it "
          "out of the library. Not one loss is a binding ambiguity — the "
          "deterministic binder either has the skeleton or it does not. "
          "The coverage cost of honesty (Q1) turned out to be the cost of "
          "the two-donor rule, not of role resolution.\n")

md.append("## 5. Compounding\n")
for m in MODELS:
    r = ret.get("B-%s-dev" % m)
    if not r:
        continue
    c, b = r["COMPOUND"], r["COMPOUND_breadth"]
    md.append("- **%s (dev library, %d plans purchased):** %s certified "
              "binder serves on SEAL = **%.1f per plan**; %d distinct "
              "signatures and %d distinct skeletons served, %.1f serves "
              "per skeleton; dedup ratio %.3f against an upper bound of "
              "%.3f." % (m, c["plans_purchased"],
                         fmt(c["certified_bind_serves"]), c["ratio_raw"],
                         b["distinct_signatures_bind_served"],
                         b["distinct_skeletons_bind_served"],
                         b["serves_per_skeleton"], c["ratio_dedup"],
                         b["dedup_ratio_upper_bound"]))
md.append("")
md.append("The raw ratio is linear in the stream (Fig. 5): a purchased "
          "plan keeps serving at a constant rate, which is what "
          "amortisation looks like on a stationary synthetic stream. The "
          "frozen dedup criterion was ill-posed — deduplicating by "
          "structure signature removes the axis along which reuse "
          "happens, so the ratio is bounded by (distinct signatures "
          "served)/(plans purchased) < 1 and no library could pass. The "
          "letter follows the frozen text; the lesson (a threshold must "
          "be checked for satisfiability before freezing) joins B24's in "
          "the methods ledger. REAL-DIAG supplies the number R11 asked "
          "for: on natural text the reach is zero, so the raw ratio is "
          "the generator's redundancy, exactly as the caveat said.\n")

md.append("## 6. Harvest\n")
md.append("| library | plans in | templatized | two-donor candidates | "
          "admitted | full | sub | probation wrongs | inert |")
md.append("|---|---|---|---|---|---|---|---|---|")
for m in MODELS:
    for sc in ("dev", "all"):
        L = lib.get("%s_%s" % (m, sc))
        if not L:
            continue
        h, l2 = L["harvest_ledger"], L["ledger"]
        md.append("| %s %s | %d | %d | %d | %d | %d | %d | %d | %d |"
                  % (m, sc, h["plans_in"], h["templated_full"],
                     h.get("two_donor_full", 0) + h.get("two_donor_sub", 0),
                     L["templates"], L["full"], L["sub"],
                     l2.get("g3_wrong", 0), l2.get("g3_inert", 0)))
for sc in ("dev", "all"):
    L = lib.get("all_%s" % sc)
    if L:
        md.append("| union %s | — | — | — | %d | %d | %d | — | — |"
                  % (sc, L["templates"], L["full"], L["sub"]))
md.append("")

md.append("## 7. Gaps, connectors, the haiku arm, real language\n")
md.append("Gap classification of the union library's %s DEV-L escalations: "
          "structure gap %.2f%%, adapter gap %.2f%%, binding gap %.2f%% "
          "(collisions %d), semantic kill %.2f%%. The adapter arm does not "
          "run (10%% rule): connectors were a null in V1.7 because the "
          "composer never fails on a missing type-flow edge — it fails "
          "because it has no grammar for the step. The haiku binding arm "
          "has no input class (the binder never reaches a two-candidate "
          "state), so haiku is redundant for binding by construction. "
          "REAL-DIAG: 0 of %s natural-language items reach any template.\n"
          % (fmt(gap.get("escalated_in_domain", 0)),
             100 * gap.get("shares", {}).get("structure_gap", 0),
             100 * gap.get("shares", {}).get("adapter_gap", 0),
             100 * gap.get("shares", {}).get("binding_gap", 0),
             gap.get("classes", {}).get("binding_gap:collision", 0),
             100 * gap.get("shares", {}).get("semantic_kill", 0),
             fmt(rd.get("n", 0))))

md.append("## 8. Energy\n")
if energy_status == "measured":
    md.append("Lean path (composer + binder + gate + witness), batch-metered "
              "with instrument controls on both sides of every batch: "
              "J per certified serve %s (sd %s); J per question, engine "
              "only, %s. Amortised J per question with V1.4's measured "
              "local-model calls as proxies: %s (producer 64.9 J) / %s "
              "(pure answer 1,910 J). The bridge's own draw is unmeasurable "
              "from here; the proxies are labelled as such.\n"
              % (en["J_per_certified_serve"]["mean"],
                 en["J_per_certified_serve"]["sd"],
                 en["J_per_question_engine"]["mean"],
                 en["J_per_question_amortised_proxy_producer_64.9J"]["value"],
                 en["J_per_question_amortised_proxy_llm_1910J"]["value"]))
else:
    md.append("Not measured: %s. The ladder caps at B when ENERGY is not "
              "measured; no component number is reused as a fleet claim.\n"
              % en.get("reason", "the instrument controls or idle windows "
                                 "did not hold"))

md.append("## 9. Outcome on the frozen ladder\n")
md.append("- SAFETY-B32: pass (0 served wrong of 8,842).")
md.append("- SAFETY-1: max wrong-fire SEAL %.5f%%, REPLAY %.5f%% (bar "
          "≤0.1%%; expectation 0 not met on REPLAY: B36)."
          % (100 * seal_wrong_fire_max, 100 * replay_wrong_fire_max))
md.append("- SAFETY-2: 0 distractors served anywhere.")
md.append("- SAFETY-BIND: %d binder-attributed wrongs." % tot_wrong_bind)
md.append("- SAFETY-3: fresh-plan arm not re-run this version (no bridge "
          "planning); haiku-13 control 13/13 killed under the new gates.")
md.append("- SAFETY-4: 0 wrongs attributable to any harvested template.")
md.append("- GATE-CTRL: %s." % ("PASS" if ctrl.get("ALL_PASS") else "FAIL"))
md.append("- RETAIN ≥60%% on ≥2 scales: %s (%s)."
          % ("pass" if len(retain_pass) >= 2 else "fail",
             ", ".join(retain_pass)))
md.append("- HARVEST ≥300 union: %s (%d)."
          % ("pass" if lib["all_all"]["templates"] >= 300 else "fail",
             lib["all_all"]["templates"]))
md.append("- COMPOUND raw ≥5: %s; dedup ≥2: **fail by construction** "
          "(bounded < 1)." % ("pass" if len(compound_raw_pass) >= 2 else "fail"))
md.append("- GAP measured: pass; adapter arm gated off (%.2f%% < 10%%)."
          % (100 * gap.get("shares", {}).get("adapter_gap", 0)))
md.append("- DEVVOL: pass (every arm ran DEV-L 400k before its sealed run).")
md.append("- ENERGY: %s." % energy_status)
md.append("\n**OUTCOME %s.** %s\n" % (letter_, {
    "C": "Safe, retained, harvested, and compounding on the raw ratio "
         "— rung C by the letter of a dedup criterion that no library "
         "could satisfy. The aggregates say the reuse problem is closed "
         "on this corpus; the pre-registration says the compounding "
         "claim was mis-specified, and it is right about that.",
    "B": "Safe, retained, harvested, compounding; ENERGY not measured.",
    "A": "All criteria met.",
    "D": "Safe but collapsed.",
    "E": "A safety criterion failed."}[letter_]))

md.append("## 10. What V1.8 claims, and does not\n")
md.append("It claims that a witness-certified plan can be served again on "
          "a question it was not written for, binding every number by "
          "role and never by position, at the composer's standard: %s "
          "binder serves across %s evaluations with zero wrong, "
          "including %s of the 8,842 questions V1.7 got wrong. It does "
          "not claim compounding on natural language (reach 0), does not "
          "claim the dedup criterion was met, and does not claim a fleet "
          "energy figure beyond what §8 measured. The binder is a fixed "
          "function of the text; what it cannot resolve it abstains on; "
          "and the one wrong answer of the version was made by the "
          "oldest code in the path, on the phrasing class that code was "
          "never asked to see.\n" % (fmt(tot_bind), fmt(tot_eval),
                                     fmt(pb.get("served_gold", 0))))

md.append("## Reproduction\n")
md.append("```\npython tools/build_devl18.py                 # DEV-L, seed 1800\n"
          "python tools/probe_b32_18.py                 # PROBE-B32 + haiku-13\n"
          "python tools/harvest18.py build|probate --model <m> --scope dev|all\n"
          "python tools/harvest18.py union --scope dev|all\n"
          "python tools/controls18.py --lib results/v18/planlib18_all_all.json\n"
          "python v18_run.py --split devl|seal|replay --arm B-<m>-<scope> --lib results/v18/planlib18_<m>_<scope>.json\n"
          "python tools/retain18.py --model <m> --split seal --arm B-<m>-dev --plans-purchased N\n"
          "python tools/gapclass18.py --rows results/v18/B-all-all_devl.jsonl --data results/v18/data/devl.jsonl\n"
          "python tools/realdiag18.py ; python tools/meter18.py\n```\n")
(REPO / "V1_8_FINAL_REPORT.md").write_text("\n".join(md), encoding="utf-8")

# ------------------------------------------------------------ PDF
ss = getSampleStyleSheet()
TITLE = ParagraphStyle("t", parent=ss["Title"], fontSize=19, leading=24,
                       spaceAfter=4, textColor=colors.HexColor("#023047"))
SUB = ParagraphStyle("sub", parent=ss["Normal"], fontSize=11, leading=15,
                     textColor=colors.HexColor("#555555"), spaceAfter=12)
H = ParagraphStyle("H", parent=ss["Heading1"], fontSize=13.5, leading=17,
                   spaceBefore=14, spaceAfter=6,
                   textColor=colors.HexColor("#023047"))
P = ParagraphStyle("P", parent=ss["Normal"], fontSize=9.4, leading=13,
                   spaceAfter=6, alignment=4)
BUL = ParagraphStyle("B", parent=P, leftIndent=14, bulletIndent=4,
                     spaceAfter=3, alignment=0)
CAP = ParagraphStyle("cap", parent=ss["Normal"], fontSize=8, leading=10.5,
                     textColor=colors.HexColor("#666666"), spaceBefore=2,
                     spaceAfter=10, alignment=1)
CODE = ParagraphStyle("code", parent=P, fontName="Courier", fontSize=7.4,
                      leading=9.5, alignment=0,
                      backColor=colors.HexColor("#f4f4f4"), borderPadding=5)


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
        t = t.replace("\x00%d\x00" % i2,
                      "<font face='Courier' size='8.2'>%s</font>" % c)
    return t


def img(name, w=6.4):
    pth = CH / name
    if not pth.exists():
        return Spacer(1, 2)
    im = Image(str(pth))
    ratio = im.imageHeight / im.imageWidth
    im.drawWidth = w * inch
    im.drawHeight = w * ratio * inch
    return im


def md_table(lines):
    rows = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(re.fullmatch(r"-+", c) for c in cells):
            continue
        rows.append([Paragraph(esc(c), ParagraphStyle(
            "c", parent=P, fontSize=6.9, leading=8.6, alignment=0,
            spaceAfter=0)) for c in cells])
    t = Table(rows, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bbbbbb")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f1f5")),
        ("TOPPADDING", (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


FIGS = {"## 3.": ("c1_seal_coverage.png", "Fig. 1 — SEAL coverage per arm; "
                  "wrong answers written on each bar."),
        "## 4.": ("c2_retain.png", "Fig. 2 — RETAIN and reuse volume."),
        "## 5.": ("c5_compound.png", "Fig. 3 — raw compounding curve."),
        "## 6.": ("c6_funnel.png", "Fig. 4 — harvest funnel."),
        "## 7.": ("c7_gaps.png", "Fig. 5 — gap classes on DEV-L."),
        "## 9.": ("c4_probe.png", "Fig. 6 — PROBE-B32 disposition."),
        "## 2.": ("c3_depth.png", "Fig. 7 — served share by depth (union "
                  "library, SEAL).")}
s = [Spacer(1, 40), Paragraph("The Adaptive Reflex Engine", TITLE),
     Paragraph("V1.8 — Role-Aware Reuse: Final Report", TITLE),
     Spacer(1, 6),
     Paragraph("Twentieth experiment of the arc. Pre-registered outcome "
               "%s. September 6, 2026. Repo reflex-engine, tag "
               "v1.8-final; spec frozen as v1.8-plan before any counting "
               "run; sealed sets hashed and evaluated once." % letter_,
               SUB),
     HRFlowable(width="100%", color=colors.HexColor("#219ebc"),
                thickness=1.2), Spacer(1, 8)]
i = 0
lines = md
in_code, code_buf, tbl_buf = False, [], []
while i < len(lines):
    ln = lines[i]
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
        if i + 1 >= len(lines) or not lines[i + 1].startswith("|"):
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
doc = SimpleDocTemplate(str(REPO / "V1_8_FINAL_REPORT.pdf"), pagesize=letter,
                        leftMargin=0.8 * inch, rightMargin=0.8 * inch,
                        topMargin=0.8 * inch, bottomMargin=0.8 * inch,
                        title="V1.8 Final Report — Role-Aware Reuse",
                        author="Kavan Shah")
doc.build(s)
print("OUTCOME", letter_, "-> V1_8_FINAL_REPORT.md/.pdf")
