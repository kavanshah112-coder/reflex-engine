# -*- coding: utf-8 -*-
# origin: new for V1.3 -- results aggregation (V1_3_SPEC section 12)
"""Collects every V1.3 measurement into one table and one verdict.

  python expanalyze_v13.py

Rules this script enforces so the report cannot overstate the run:

  * ARMS WITH UNRESOLVED ITEMS are reported with the unresolved count
    visible, and those items are scored as ABSTENTIONS, never dropped.
    Dropping them would silently raise coverage.
  * THE OPUS ARM IS EXCLUDED from every cross-model claim (B9): its
    servicing agent read the verifier, so its pass rate measures the
    checks' gameability, not a model's reading.
  * NO ENERGY OR COST FIGURE is computed from bridge arms (B7), whose
    token fields were fabricated by servicing agents. Only the local
    arm can carry one.
  * WRONG-FIRE IS REPORTED WHETHER OR NOT IT IS ZERO, per family, per
    corpus, per arm.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V13 = HERE / "results" / "v13"


def load(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


def arms():
    out = []
    for f in sorted((V13 / "w2").glob("*_arm_sample_summary.json")):
        d = load(f, {})
        st = d.get("status", {})
        unresolved = st.get("pending", 0) + \
            st.get("abstained_unresolved", 0)
        served = st.get("certified", 0)
        out.append({
            "arm": d.get("tag", f.stem), "n": d.get("n", 0),
            "certified": served,
            "correct": st.get("correct", 0),
            "wrong": st.get("WRONG", 0),
            "corroboration_abstain": st.get("corroboration_mismatch", 0),
            "verification_failed": st.get("verification_failed", 0),
            "model_refused": st.get("model_refused", 0),
            "unresolved": unresolved,
            "first_failing": d.get("first_failing_check", {}),
            "coverage": round(served / d["n"], 4) if d.get("n") else None,
            "wrong_fire": (round(st.get("WRONG", 0) / served, 4)
                           if served else 0.0),
            "excluded_from_model_claims":
                "opus" in (d.get("tag") or ""),
            "token_source": d.get("token_source", "measured"),
        })
    return out


def rag():
    out = []
    for f in sorted((V13 / "w6").glob("w6_*_summary.json")):
        d = load(f, {})
        st = d.get("status", {})
        served = st.get("certified", 0) + st.get("answered", 0)
        out.append({
            "corpus": d.get("corpus"), "arm": d.get("arm"),
            "n": d.get("n"), "served": served,
            "correct": st.get("correct", 0),
            "wrong": st.get("WRONG", 0),
            "abstained": st.get("abstained", 0),
            "pending": st.get("pending", 0),
            "retrieval_recall": d.get("retrieval_recall"),
            "by_family": d.get("by_family", {}),
            "wrong_fire": (round(st.get("WRONG", 0) / served, 4)
                           if served else 0.0)})
    return out


def main():
    rep = {"w0_recurrence": None, "w1_frame": None, "w2_arms": arms(),
           "w5_plan_reflexes": {}, "w6_rag": rag(), "w7": None}

    w0 = load(V13 / "w0_recurrence.json", {})
    if w0:
        lv = w0.get("levels", {}).get("medium", {})
        rep["w0_recurrence"] = {
            "pool": w0.get("pool_n"), "parsed": w0.get("parsed"),
            "distinct_medium": lv.get("distinct"),
            "top200_coverage": lv.get("top200_coverage"),
            "gate": 0.35,
            "verdict": ("L1 CONFIRMED"
                        if (lv.get("top200_coverage") or 0) >= 0.35
                        else "L1 FALSIFIED")}

    w1 = load(V13 / "w1_frame_summary.json", {})
    if w1:
        rep["w1_frame"] = w1

    for mode in ("repeat", "unique"):
        for suf in ("", "_corrob"):
            d = load(V13 / "w5" / f"w5_{mode}{suf}_summary.json")
            if d:
                rep["w5_plan_reflexes"][mode + (suf or "_plain")] = {
                    "corpus_plans": d.get("corpus_verified_plans"),
                    "hit_rate": d.get("cache_hit_rate"),
                    "served": d.get("status", {}).get("cache_served"),
                    "wrong": d.get("status", {}).get("CACHE_WRONG"),
                    "wrong_fire": d.get("wrong_fire_rate"),
                    "schemas": d.get("cache", {}).get("schemas")}

    sc = load(HERE / "results/certification/safety_case.json", {})
    rep["w7"] = {"tier_a": sc.get("tier_a"),
                 "tier_b": sc.get("tier_b"),
                 "verdict": sc.get("verdict")}

    clean = [a for a in rep["w2_arms"]
             if not a["excluded_from_model_claims"]]
    served = sum(a["certified"] for a in clean)
    wrong = sum(a["wrong"] for a in clean)
    # Only the FULL-corpus R3 runs count toward the headline. The
    # --limit 120 runs are a SUBSET of the same queries; summing both
    # would count 117 answers twice and inflate the denominator.
    rag_f = [r for r in rep["w6_rag"]
             if r["arm"] == "r3" and r["n"] == 300]
    rserved = sum(r["by_family"].get("factual", {}).get("served", 0)
                  for r in rag_f)
    rwrong = sum(r["by_family"].get("factual", {}).get("WRONG", 0)
                 for r in rag_f)
    rep["headline"] = {
        "arithmetic_real_language": {
            "arms_counted": [a["arm"] for a in clean],
            "certified": served, "wrong": wrong,
            "wrong_fire": round(wrong / served, 5) if served else None},
        "retrieval_non_arithmetic": {
            "certified": rserved, "wrong": rwrong,
            "wrong_fire": (round(rwrong / rserved, 5)
                           if rserved else None)},
        "unresolved_scored_as_abstention":
            sum(a["unresolved"] for a in rep["w2_arms"]),
        "excluded_arms": [a["arm"] for a in rep["w2_arms"]
                          if a["excluded_from_model_claims"]],
        "energy_claim": "NOT COMPUTED FROM BRIDGE ARMS (B7)"}

    out = V13 / "v13_results.json"
    out.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(json.dumps(rep["headline"], indent=1))
    print()
    print("%-22s %5s %6s %6s %6s %6s %6s"
          % ("arm", "n", "cert", "corr", "WRONG", "abst", "unres"))
    for a in rep["w2_arms"]:
        print("%-22s %5s %6s %6s %6s %6s %6s%s"
              % (a["arm"], a["n"], a["certified"], a["correct"],
                 a["wrong"], a["corroboration_abstain"],
                 a["unresolved"],
                 "  [EXCLUDED B9]" if a["excluded_from_model_claims"]
                 else ""))
    print()
    print("%-10s %-4s %5s %6s %6s %6s  %s"
          % ("corpus", "arm", "n", "served", "corr", "WRONG",
             "recall"))
    for r in rep["w6_rag"]:
        print("%-10s %-4s %5s %6s %6s %6s  %s"
              % (r["corpus"], r["arm"], r["n"], r["served"],
                 r["correct"], r["wrong"], r["retrieval_recall"]))
    print("\\nwrote", out)


if __name__ == "__main__":
    main()
