# -*- coding: utf-8 -*-
# origin: new for V1.7 -- the frozen plan schema (SPEC 4)
"""One plan format for everything: the builder's reference DAGs, the
deterministic composer's output, model-proposed plans, and chain
reflexes. Frozen at v1.7-plan; the gate validates against THIS.

    plan = {
      "nodes": [ {"id": "n1", "op": <op>, <slot>: literal | "@nX"},
                 ... ],
      "final": "nK",
    }

Ops: every symcore16 op, plus
    "convert"  {value: @ref|num, "from": unit, "to": unit}
    "scale"    {value: @ref|num, "by": num}       (exact scalar)
    "formula"  {"expr": <witness-grammar expr over named slots>,
                <slot>: @ref|num, ...}            (physics/finance)
A "@nX" reference consumes node nX's output. No node may carry a
producer-supplied ANSWER; literals are operands only. DAG only, one
final node, every node reachable from final (checked by the gate,
not assumed here).

`signature(plan)` is the structure key for plan REUSE (SPEC 5/7 V7):
ops + edge shape + slot names, with every literal blanked — two
queries share a signature iff the same plan shape answers both.
"""
import json
import re

REF = re.compile(r"^@n\d+$")

STRUCTURAL_KEYS = ("op",)


def is_ref(v):
    return isinstance(v, str) and REF.match(v) is not None


def refs_in(node):
    out = []
    for k, v in node.items():
        if k in ("id",):
            continue
        if is_ref(v):
            out.append((k, v[1:]))
        elif isinstance(v, str):
            for m in re.finditer(r"@(n\d+)\b", v):
                out.append((k, m.group(1)))
    return out


def signature(plan):
    """Structure-only key: literals blanked, refs kept positionally."""
    sig = []
    for node in plan.get("nodes", []):
        row = {"op": node.get("op")}
        for k, v in sorted(node.items()):
            if k in ("id", "op"):
                continue
            if is_ref(v):
                row[k] = v
            elif isinstance(v, str) and "@" in v:
                row[k] = re.sub(r"-?\d+(?:\.\d+)?", "#", v)
            else:
                row[k] = "#"
        sig.append(row)
    return json.dumps({"nodes": sig, "final": plan.get("final")},
                      sort_keys=True)
