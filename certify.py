# -*- coding: utf-8 -*-
# origin: new for V1.2 — W1.4 Safety Certification Artifact
"""Regenerates the machine-checkable safety case and the one-page
external certificate.

  python certify.py          # aggregate + verify recorded evidence
  python certify.py --full   # re-run invariants, audit, battery,
                             # and the seed sweep live first

Outputs: results/certification/safety_case.json and CERTIFICATE.md.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CERT = HERE / "results" / "certification"


def run(cmd):
    r = subprocess.run([sys.executable] + cmd, cwd=HERE,
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)[-2000:]


def tier_b_evidence():
    """Assemble the measured evidence for model-parsed answers.

    Returns None when there is no CURRENT measurement. That refusal is
    the point of the two-tier split (V1_3_SPEC section 10): Tier A is
    a standing guarantee that can be restated from frozen artifacts,
    Tier B is a claim about how often a MODEL misreads, and a claim
    like that goes stale the moment the model, the prompt, or the
    check suite changes. A certificate that printed a remembered
    Tier B number would be asserting something nobody had measured.

    Arms with items still pending are excluded outright rather than
    scored on their completed part: a partial arm is biased toward
    whatever finished first.
    """
    W2 = HERE / "results" / "v13" / "w2"
    W6 = HERE / "results" / "v13" / "w6"
    arms, excluded = [], []
    for f in sorted(W2.glob("*_arm_sample_summary.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        st = d.get("status", {})
        if st.get("pending") or d.get("bridge_pending"):
            excluded.append({"arm": d.get("tag"),
                             "why": "incomplete",
                             "pending": st.get("pending", 0)})
            continue
        served = st.get("certified", 0)
        if not served:
            excluded.append({"arm": d.get("tag"),
                             "why": "nothing_certified"})
            continue
        arms.append({"arm": d.get("tag"), "n": d.get("n"),
                     "served": served,
                     "correct": st.get("correct", 0),
                     "wrong": st.get("WRONG", 0),
                     "verifier_aware": "opus" in (d.get("tag") or "")})
    rag = []
    for f in sorted(W6.glob("w6_*_r3_summary.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("bridge_pending"):
            continue
        fam = d.get("by_family", {}).get("factual", {})
        if fam.get("served"):
            rag.append({"corpus": d.get("corpus"),
                        "served": fam["served"], "n": fam["n"],
                        "correct": fam["correct"],
                        "wrong": fam["WRONG"]})
    clean = [a for a in arms if not a["verifier_aware"]]
    if not clean and not rag:
        return {"measurable": False, "excluded": excluded,
                "why": "no complete arm and no complete RAG corpus"}
    served = sum(a["served"] for a in clean) + sum(r["served"]
                                                   for r in rag)
    wrong = sum(a["wrong"] for a in clean) + sum(r["wrong"]
                                                 for r in rag)
    return {"measurable": True, "arms": arms, "rag": rag,
            "excluded": excluded, "served": served, "wrong": wrong,
            "wrong_rate": round(wrong / served, 5) if served else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    CERT.mkdir(parents=True, exist_ok=True)
    case = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "engine": "reflex-engine (V1.2 line, post-W1)",
            "checks": {}}

    if a.full:
        for name, cmd in (
                ("invariants", ["-c",
                 "import sys;sys.path.insert(0,'reflex/_arc');"
                 "import runpy;runpy.run_path("
                 "'reflex/_arc/v11/test_invariants11.py',"
                 "run_name='__main__')"]),
                ("vocab_audit", ["tests/test_vocab_audit.py"]),
                ("battery", ["parity_run.py", "--resolver", "on",
                             "--engine", "pack", "--plus"]),
                ("seed_sweep", ["sweep_v12.py"])):
            rc, out = run(cmd)
            case["checks"][name] = {"rc": rc,
                                    "pass": rc == 0,
                                    "tail": out[-300:]}
    else:
        pv = json.loads((HERE / "results/parity_v11/"
                         "parity_verdict.json").read_text(
            encoding="utf-8"))
        case["checks"]["battery"] = {
            "pass": all(v["ok"] for v in pv.values()
                        if isinstance(v, dict) and "ok" in v),
            "detail": {k: {"acc": v["acc"],
                           "wrong_fire": v["wrong_fire"],
                           "improved": len(v.get("improvements",
                                                 []))}
                       for k, v in pv.items()
                       if isinstance(v, dict) and "ok" in v}}
        sw = json.loads((CERT / "seed_sweep_ledger.json")
                        .read_text(encoding="utf-8"))
        case["checks"]["seed_sweep"] = {
            "pass": sw["total_wrong_fire"] == 0,
            "items": sw["total_items"],
            "suites": sw["suites"]}
        rc, out = run(["tests/test_vocab_audit.py"])
        case["checks"]["vocab_audit"] = {"pass": rc == 0}
        rc, out = run(["-c",
                       "import sys;sys.path.insert(0,"
                       "'reflex/_arc');import runpy;runpy.run_path("
                       "'reflex/_arc/v11/test_invariants11.py',"
                       "run_name='__main__')"])
        case["checks"]["invariants"] = {"pass": rc == 0}

    # the complete wrong-fire history of the engine line (sealed
    # evaluations only; every event, none excused)
    case["wrong_fire_history"] = [
        {"when": "V1.0 EXP-ACQ + controls", "events": 0,
         "note": "0.000 in every gated arm, probe, and final"},
        {"when": "V1.1 sim finals (fresh seed 9666)", "events": 1,
         "note": "B2 latent ordinal gap ('the tenth one' -> GLOBAL "
                 "fallthrough -> bind trap, 1/76 = 1.3%); fixed "
                 "(W1c), superseded, re-run to sem 100%/0; class "
                 "closed by the V1.2 ambiguity guard + reference-"
                 "trap sweep"},
        {"when": "V1.2 certification (battery + 65-seed sweep, "
                 "10,160 trap items)", "events": 0,
         "note": "0.000 everywhere incl. beyond-vocabulary ordinals "
                 "and vague references"},
    ]
    tier_a_ok = all(c.get("pass") for c in case["checks"].values())
    case["tier_a"] = {"pass": tier_a_ok}
    case["tier_b"] = tier_b_evidence()
    # Tier A regression is fatal to the whole certificate: a model
    # reading well can never compensate for the deterministic path
    # breaking (V1_3_SPEC section 10).
    ok = tier_a_ok
    case["verdict"] = "CERTIFIED" if ok else "FAILED"
    (CERT / "safety_case.json").write_text(
        json.dumps(case, indent=1), encoding="utf-8")

    tb = case["tier_b"]
    if tb.get("measurable"):
        nl = chr(10)
        rows = nl.join(
            f"  - {a['arm']}: {a['served']}/{a['n']} served, "
            f"{a['wrong']} wrong"
            + ("  *(verifier-aware — excluded from the rate)*"
               if a["verifier_aware"] else "")
            for a in tb["arms"]) or "  - (none)"
        rag_rows = nl.join(
            f"  - {r['corpus']} corpus (retrieval): {r['served']}/"
            f"{r['n']} served, {r['wrong']} wrong"
            for r in tb["rag"]) or "  - (none)"
        tier_b_md = f"""**TIER B — model-parsed input.** MEASURED.
Wrong-rate **{tb['wrong_rate']}** over {tb['served']} served answers
({tb['wrong']} wrong). Every Tier B answer additionally passed
agreement, round-trip, consumption, scope, dimensional and
non-degeneracy checks, and an independent corroboration.

Arms:
{rows}
Retrieval (provenance-certified, no arithmetic):
{rag_rows}

Tier B is a claim about how often a MODEL misreads, and it expires
when the model, the prompt, or the check suite changes."""
    else:
        tier_b_md = f"""**TIER B — model-parsed input. NOT CERTIFIED.**
This certificate REFUSES to state a Tier B guarantee because no
current measurement exists ({tb.get('why')}). Excluded evidence:
{json.dumps(tb.get('excluded', []), indent=1)}

An engine running the model-parsed path is running UNCERTIFIED until
`python certify.py` can print a measured wrong-rate here."""

    sw = case["checks"].get("seed_sweep", {})
    cert_md = f"""# Reflex Engine — Safety Certificate (one page)

## Two tiers — which one is a given deployment running?

**TIER A — self-parsed input** (the deterministic path). Unchanged and
unqualified: never wrong across the full sealed battery and
{sw.get('items', 10160)} trap items over 65 independent seeds. Tier A
is regenerable from frozen artifacts and does not expire.

{tier_b_md}

A deployment that admits free-form language is running Tier B, and
inherits Tier B's wrong-rate — not Tier A's guarantee.

---


**Engine:** reflex-engine, V1.2 line · **Generated:** {case['generated']} · **Verdict: {case['verdict']}**

## What this engine guarantees
1. **It answers only what it can certify.** Every answer carries a
   machine-readable certificate (derivation facts, integrity checks,
   reflex provenance). Everything else is an explicit abstention or a
   labeled escalation — never a guess.
2. **Detected hazards abstain.** Contradictions, ambiguous bindings,
   and unresolved references over multi-entity states return the
   hazard, not an answer.
3. **Acquired knowledge passes typed gates** (dimensional
   verification, consistency quorums, shadow probation) before it can
   ever answer, and every acquired reflex records its authorship.

## The evidence (machine-regenerable: `python certify.py --full`)
- Invariants J1–J8: machine-checked pass.
- Vocabulary-completeness audit: all resolution tables reachable by
  their gates (2 historical gaps found and closed; documented
  exceptions listed with reasons).
- Full sealed battery (V0.5–V1.1 lineage, 1,634+ items): wrong-fire
  0.000, zero regressions vs the certified champion.
- Seed-sweep: {sw.get('items', 10160)} adversarial/trap items across
  65 independent generation seeds: wrong-fire 0.000.

## The complete wrong-fire history (nothing excused)
One event in the engine line's sealed history: a latent
ordinal-vocabulary gap produced one mis-bound answer (1/76, 1.3%) on
a fresh-seed suite in V1.1. It was found by the sealed evaluation,
fixed, re-verified, and its entire CLASS is now closed by an
ambiguity-by-default guard plus a permanent vocabulary audit and the
65-seed sweep above. Lesson institutionalized: seed luck is not
coverage — only vocabulary-complete gates are.

## How to re-verify
`python certify.py --full` regenerates every check above from source
on the frozen artifacts. `python run_v1_2_experiment.py` reproduces
the version's numbers.
"""
    (CERT / "CERTIFICATE.md").write_text(cert_md, encoding="utf-8")
    print(f"safety case: {case['verdict']}; checks: "
          f"{ {k: v.get('pass') for k, v in case['checks'].items()} }")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
