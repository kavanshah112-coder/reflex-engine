# -*- coding: utf-8 -*-
# origin: new for V1.8 -- escalation gap classification (SPEC 4.3)
"""Classifies every escalated in-domain item of a v18_run row file by
the composer's and binder's own failure reasons:

  structure_gap   composer found no DAG and no template skeleton
                  matched -- nobody had a structure
  adapter_gap     composer built a DAG that died on unit flow (G-P2)
                  or the ask-unit check (G-P3 'asked in') -- a missing
                  type-flow edge
  semantic_kill   composer DAG killed at G-P4/G-P4'/G-P5 (honesty,
                  usage, formula) -- the gate refused a structure
  binding_gap:*   a template skeleton matched but the binder
                  abstained (unresolved / unbound_slot / collision /
                  gate:* / exec_refused / donor_self)
  other           anything else (v16-path escalations on non-chain
                  text, exec refusals)

  python tools/gapclass18.py --rows results/v18/<arm>_<split>.jsonl
        [--data results/v18/data/devl.jsonl]   (to skip distractors)
"""
import argparse
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def classify(r):
    comp = r.get("comp") or ""
    reason = r.get("reason") or ""
    if reason and reason != "no_skeleton":
        return "binding_gap:" + reason.split(":")[0] + (
            ":" + reason.split(":")[1] if reason.startswith("gate:")
            else "")
    if comp.startswith("gate:G-P2") or (comp.startswith("gate:G-P3") and
                                        "asked in" in comp):
        return "adapter_gap"
    if comp.startswith("gate:G-P3"):
        return "semantic_kill:G-P3"
    if comp.startswith("gate:"):
        return "semantic_kill:" + comp.split(":")[1]
    if comp == "none":
        return "structure_gap"
    if comp == "exec_refused":
        return "other:composer_exec_refused"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--data", default=None)
    a = ap.parse_args()
    dist = set()
    if a.data:
        with open(a.data, encoding="utf-8") as f:
            for line in f:
                it = json.loads(line)
                if it.get("distractor"):
                    dist.add(it["id"])
    c = Counter()
    n_esc = 0
    with open(a.rows, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("served") or r["id"] in dist:
                continue
            n_esc += 1
            c[classify(r)] += 1
    top = {"structure_gap": 0, "adapter_gap": 0, "semantic_kill": 0,
           "binding_gap": 0, "other": 0}
    for k, v in c.items():
        top[k.split(":")[0]] += v
    res = {"rows": a.rows, "escalated_in_domain": n_esc,
           "classes": dict(c),
           "shares": {k: round(v / n_esc, 4) if n_esc else None
                      for k, v in top.items()},
           "adapter_gap_share": round(top["adapter_gap"] / n_esc, 4)
           if n_esc else None,
           "adapter_arm_runs": (top["adapter_gap"] / n_esc >= 0.10)
           if n_esc else None}
    out = Path(a.rows).with_name(Path(a.rows).stem + "_gapclass.json")
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
