# -*- coding: utf-8 -*-
# origin: new for V1.7 -- plan REUSE library builder (SPEC 5, V7)
"""Generalizes each admitted (question, plan) pair into a replayable
template, honestly: only the model's own input (the question text)
and output (its plan) are used -- never the dataset's reference
structure.

Mechanism: every number token in the source question becomes a named
regex group; every plan literal equal to one of those numbers becomes
a $group reference. A plan literal that matches no question number
must be a STRUCTURAL constant (0.5, 100, 1000, 9.8, 3.6, small ints)
or the pair is skipped (it would not generalize). The result is a
chain-reflex-shaped entry {name, pattern, plan} that the runner's
mint-chain path executes behind the FULL gate + witness on every
replay serve -- reuse extends reach, never trust.

  python tools/planlib17.py build --model <m> --phase dev
      reads results/v17/planlib_<m>_<phase>.json (admitted plans)
      + the split items for their question texts, writes
      results/v17/replaylib_<m>_<phase>.json and prints how many
      pairs template-ized cleanly.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
DATA = HERE / "results" / "v17" / "data"
RES = HERE / "results" / "v17"

STRUCTURAL = {0.0, 1.0, 2.0, 0.5, 100.0, 1000.0, 9.8, 3.6, 60.0}
NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _load_split(name):
    out = {}
    with open(DATA / ("q1m_%s.jsonl" % name), encoding="utf-8") as f:
        for line in f:
            it = json.loads(line)
            out[it["id"]] = it
    return out


def templateize(question, plan):
    """-> {pattern, plan} or None."""
    nums = []
    parts = []
    last = 0
    for i, m in enumerate(NUM.finditer(question)):
        parts.append(re.escape(question[last:m.start()]))
        g = "g%d" % i
        nums.append((g, float(m.group(0))))
        parts.append(r"(?P<%s>-?\d+(?:\.\d+)?)" % g)
        last = m.end()
    parts.append(re.escape(question[last:]))
    pattern = "^" + "".join(parts) + "$"
    if not nums:
        return None
    byval = {}
    for g, v in nums:
        byval.setdefault(v, []).append(g)

    def sub_literal(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            fv = float(v)
            if fv in byval:
                return "$" + byval[fv][0]
            if fv in STRUCTURAL or (fv.is_integer() and 0 <= fv <= 6):
                return v
            return None                    # non-generalizable literal
        if isinstance(v, str):
            # numbers inside expressions: replace question-matched
            # ones with $refs; leave structural ones
            bad = []

            def rep(mm):
                fv = float(mm.group(0))
                if fv in byval:
                    return "$" + byval[fv][0]
                if fv in STRUCTURAL or (fv.is_integer() and
                                        0 <= fv <= 9):
                    return mm.group(0)
                bad.append(fv)
                return mm.group(0)
            s = NUM.sub(rep, v)
            if bad:
                return None
            return s
        return v

    nodes = []
    for node in plan.get("nodes", []):
        nd = {}
        for k, v in node.items():
            if k in ("id", "op", "from", "to", "var", "pick", "unit"):
                nd[k] = v
                continue
            sv = sub_literal(v)
            if sv is None:
                return None
            nd[k] = sv
        nodes.append(nd)
    return {"pattern": pattern,
            "plan": {"nodes": nodes, "final": plan.get("final")}}


def build(model, phase):
    split = "dev" if phase == "dev" else "seal"
    items = _load_split(split)
    admitted = json.loads(
        (RES / ("planlib_%s_%s.json" % (model, phase)))
        .read_text(encoding="utf-8"))
    out, skipped = [], 0
    for i, a in enumerate(admitted):
        it = items.get(a["id"])
        if it is None:
            skipped += 1
            continue
        t = templateize(it["text"], a["plan"])
        if t is None:
            skipped += 1
            continue
        out.append({"cls": "chain",
                    "name": "%s_plan_%04d" % (model, i),
                    "pattern": t["pattern"], "plan": t["plan"],
                    "sig": a.get("sig")})
    (RES / ("replaylib_%s_%s.json" % (model, phase))).write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({"model": model, "phase": phase,
                      "admitted": len(admitted),
                      "templated": len(out), "skipped": skipped}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--phase", default="dev",
                    choices=["dev", "sealed"])
    a = ap.parse_args()
    build(a.model, a.phase)


if __name__ == "__main__":
    main()
