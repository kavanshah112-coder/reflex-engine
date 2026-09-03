# -*- coding: utf-8 -*-
# origin: new for V1.7 -- chain fact sheets for bridge authoring
"""Fact-first CHAIN items: a reference plan + gold (independent
witness replay) + a neutral step-by-step BRIEF for a bridge author
to phrase as ONE natural multi-step question. Authors see only the
brief (B9); their text replaces the item's own-register text via
merge_foreign17.

  python tools/gen_factsheets17.py --n 6000

Seed 1701 (disjoint from the Q-1M generator's 1700). Reuses the
builder's chain generator so foreign sheets share the frozen depth
recipe; the brief describes each step in plain words with every
number fixed.
"""
import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tools"))
from build_q1m import K_MIX, gen_item  # noqa: E402

SEED = 1701


def _brief_step(node, first):
    op = node["op"]
    ref = "the previous result"
    if op == "solve_pick":
        return "find the %s root of %s = %s" % (
            node.get("pick", "larger"),
            node["lhs"].replace("**", "^"), node.get("rhs", "0"))
    if op == "derivative_at":
        ow = {1: "first", 2: "second", 3: "third"}[
            int(node.get("order", 1))]
        return "take the %s derivative of %s at x = %g" % (
            ow, node["expr"].replace("**", "^"), node["point"])
    if op == "integrate_def":
        return "integrate %s from %g to %g" % (
            node["expr"].replace("**", "^"), node["a"], node["b"])
    if op in ("gcd", "lcm"):
        return "take the %s of %d and %d" % (op, node["a"], node["b"])
    if op == "ncr":
        return "compute %d choose %d" % (node["n"], node["r"])
    if op == "sum_finite":
        return "sum %s for %s from %d to %d" % (
            node["expr"].replace("**", "^"), node.get("var", "k"),
            node["a"], node["b"])
    if op == "scale":
        return "multiply %s by %g" % (ref, node["by"])
    if op == "evaluate":
        e = node["expr"]
        if "@" in e:
            import re
            e = re.sub(r"@n\d+", "R", e)
            return "compute %s where R is %s" % (
                e.replace("**", "^"), ref)
        return "compute %s" % e.replace("**", "^")
    if op == "formula":
        binds = ", ".join("%s = %s" % (k, "the previous result"
                                       if str(v).startswith("@")
                                       else v)
                          for k, v in node.items()
                          if k not in ("id", "op", "expr", "unit"))
        return "apply the formula %s with %s" % (
            node["expr"].replace("**", "^"), binds)
    if op == "convert":
        return "convert %s from %s to %s" % (ref, node["from"],
                                             node["to"])
    if op == "compare":
        return "state whether %s is greater than %g" % (ref,
                                                        node["b"])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=6000)
    ap.add_argument("--out", default=str(HERE / "results" / "v17" /
                                         "data" / "factsheets17.json"))
    a = ap.parse_args()
    rng = random.Random(SEED)
    sheets, rejects = [], 0
    ks = [k for k, f in K_MIX for _ in range(int(f * 100))]
    while len(sheets) < a.n:
        k = ks[rng.randrange(len(ks))]
        it = gen_item(rng, k)
        if it is None:
            rejects += 1
            continue
        steps = []
        bad = False
        for i, node in enumerate(it["plan"]["nodes"]):
            b = _brief_step(node, i == 0)
            if b is None:
                bad = True
                break
            steps.append("%d) %s" % (i + 1, b))
        if bad:
            rejects += 1
            continue
        unit_note = ""
        if it["gold_type"] == "num" and ", in " in it["text"]:
            unit_note = (" The question must ask for the final "
                         "answer in the unit named by the last "
                         "conversion step.")
        brief = ("Write ONE natural multi-step question, calculator/"
                 "exam register, that walks through these steps IN "
                 "ORDER, each step feeding the next. Keep every "
                 "number, function and unit exactly as given; do not "
                 "reveal intermediate answers.%s Steps: %s"
                 % (unit_note, " ".join(steps)))
        sheets.append({"sheet_id": "fs17_%05d" % len(sheets),
                       "brief": brief, "plan": it["plan"],
                       "gold": it["gold"],
                       "gold_type": it["gold_type"], "k": it["k"],
                       "leaves": it["leaves"],
                       "nonmono": it["nonmono"],
                       "multidomain": it["multidomain"],
                       "sig": it["sig"]})
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(sheets, indent=0),
                           encoding="utf-8")
    print(json.dumps({"sheets": len(sheets), "rejects": rejects}))


if __name__ == "__main__":
    main()
