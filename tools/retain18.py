# -*- coding: utf-8 -*-
# origin: new for V1.8 -- RETAIN and COMPOUND metrics (SPEC 8 b, d; 9)
"""
  python tools/retain18.py --model <m> --split seal --arm B-<m>-dev
        [--plans-purchased N]

RETAIN  role-aware template serves / V1.7 positional template serves
        on the SAME items: denominator = items the R-<model> arm
        served via 'mint:chain:<model>_plan_*' (dev-phase replay
        templates, right or wrong); numerator = those same items the
        V1.8 arm served via 'bind:*' (all correct by SAFETY-BIND, or
        the wrong is reported). Also: binder serves on items V1.7 did
        NOT template-serve (new coverage), and the abstain-reason
        anatomy on the denominator items.
COMPOUND certified library serves / plans purchased, raw over the
        stream and on the signature-deduplicated stream (first item
        of each gold `sig`), plus the cumulative curve.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
V17 = HERE / "results" / "v17"
OUT = HERE / "results" / "v18"


def _rows(p):
    with open(p, encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--split", default="seal")
    ap.add_argument("--arm", required=True)
    ap.add_argument("--plans-purchased", type=int, default=0)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    tag = ("_%s" % a.tag) if a.tag else ""
    v17 = {r["id"]: r for r in _rows(V17 / ("R-%s_%s.jsonl"
                                            % (a.model, a.split)))}
    v18 = {r["id"]: r for r in _rows(OUT / ("%s_%s%s.jsonl"
                                            % (a.arm, a.split, tag)))}
    prefix = "mint:chain:%s_plan_" % a.model
    den = [i for i, r in v17.items() if (r.get("path") or "")
           .startswith(prefix)]
    num = [i for i in den if (v18.get(i, {}).get("path") or "")
           .startswith("bind:")]
    num_correct = [i for i in num if v18[i].get("correct")]
    v17_wrong_in_den = [i for i in den if v17[i].get("correct") is False]
    reasons = Counter((v18.get(i, {}).get("reason") or
                       ("served:" + (v18.get(i, {}).get("path") or "?")
                        .split(":")[0]))
                      for i in den if i not in num)
    new_cov = [i for i, r in v18.items() if (r.get("path") or "")
               .startswith("bind:") and i not in set(den)]
    new_from = Counter((v17.get(i, {}).get("path") or "escalated")
                       .split(":")[0] for i in new_cov)
    res = {"model": a.model, "split": a.split, "arm": a.arm,
           "v17_template_serves": len(den),
           "v17_template_wrong": len(v17_wrong_in_den),
           "v18_bind_on_same": len(num),
           "v18_bind_on_same_correct": len(num_correct),
           "RETAIN": round(len(num) / len(den), 4) if den else None,
           "abstain_anatomy_on_denominator": dict(reasons),
           "bind_new_coverage": len(new_cov),
           "bind_new_coverage_v17_path": dict(new_from)}
    # COMPOUND
    if a.plans_purchased:
        sigs = {}
        with open(V17 / "data" / ("q1m_%s.jsonl" % a.split),
                  encoding="utf-8") as f:
            for line in f:
                it = json.loads(line)
                sigs[it["id"]] = it.get("sig")
        seen = set()
        binds = 0
        binds_dedup = 0
        curve = []
        n = 0
        for i, r in v18.items():
            n += 1
            b = (r.get("path") or "").startswith("bind:") and \
                r.get("correct")
            if b:
                binds += 1
            s = sigs.get(i)
            if s is not None and s not in seen:
                seen.add(s)
                if b:
                    binds_dedup += 1
            if n % 50000 == 0:
                curve.append({"n": n, "binds": binds,
                              "ratio": round(binds / a.plans_purchased,
                                             3)})
        res["COMPOUND"] = {"plans_purchased": a.plans_purchased,
                           "certified_bind_serves": binds,
                           "ratio_raw": round(binds / a.plans_purchased,
                                              3),
                           "unique_signatures": len(seen),
                           "certified_bind_serves_dedup": binds_dedup,
                           "ratio_dedup": round(
                               binds_dedup / a.plans_purchased, 3),
                           "curve": curve}
    p = OUT / ("retain_%s_%s%s.json" % (a.arm, a.split, tag))
    p.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
