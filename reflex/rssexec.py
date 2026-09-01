# -*- coding: utf-8 -*-
# origin: new for V1.4 -- deterministic execution over the substrate
"""Computes the answer, once every check has agreed the state means
what it appears to mean.

The engine does all arithmetic. No number a producer wrote is ever
returned as an answer -- producers supply node CONTENTS lifted verbatim
from the query, and every derived value here is computed from them by
an operator the engine resolved. That is V1.3's invariant carried
forward unchanged; what is new is that the operator is resolved rather
than asserted.

Execution follows the state's own ordering. A derived node names the
node it came from and the event that produced it, so evaluation walks
that chain rather than reconstructing one -- which is what makes
`90 - (49 - 19)` inexpressible rather than merely wrong: the chain
either points at the superseded state or it does not, and the
grouping is fixed before any arithmetic happens.
"""
import re

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

OPS = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "div": lambda a, b: a / b if b else None,
}


def _num_in(span):
    m = NUM.findall((span or "").replace(",", ""))
    try:
        return float(m[0]) if m else None
    except ValueError:
        return None


def execute(state):
    """-> (value, trace). value is None when the state cannot be
    evaluated, which is an abstention, never a guess."""
    vals = {}
    trace = []
    for n in state.nodes.values():
        if isinstance(n.get("content"), (int, float)):
            vals[n["id"]] = float(n["content"])

    # Evaluate derived nodes in order. A node is ready when its source
    # node has a value and its relation resolved.
    pending = [n for n in state.nodes.values()
               if n["id"] not in vals and n.get("derived_from")]
    pending.sort(key=lambda n: (n.get("order") if n.get("order")
                                is not None else 1e9, n["id"]))
    progressed = True
    while pending and progressed:
        progressed = False
        still = []
        for n in pending:
            srcs = [state.get(d) for d in (n.get("derived_from") or [])]
            src_nodes = [s for s in srcs if s and s["id"].startswith("n")]
            src_rels = [s for s in srcs if s and s["id"].startswith("r")]
            if not src_rels or not src_nodes:
                still.append(n)
                continue
            r = src_rels[0]
            op = (r.get("resolved") or {}).get("op")
            base_id = src_nodes[0]["id"]
            if op not in OPS or base_id not in vals:
                still.append(n)
                continue
            operand = None
            others = [a for a in r["args"] if a != base_id and a in vals]
            if others:
                operand = vals[others[0]]
            else:
                operand = _num_in(r.get("span"))
            if operand is None:
                still.append(n)
                continue
            out = OPS[op](vals[base_id], operand)
            if out is None:
                still.append(n)
                continue
            vals[n["id"]] = out
            trace.append({"node": n["id"], "op": op,
                          "base": vals[base_id], "operand": operand,
                          "value": out})
            progressed = True
        pending = still

    if pending:
        return None, {"why": "unevaluable nodes",
                      "nodes": [n["id"] for n in pending]}

    terms = [t for t in state.terminals() if t["id"] in vals]
    if not terms:
        return None, {"why": "no evaluable terminal"}
    if len(terms) > 1:
        derived = [t for t in terms if t.get("derived_from")]
        if len(derived) == 1:
            terms = derived
        else:
            return None, {"why": "multiple terminals",
                          "terminals": [t["id"] for t in terms]}
    t = terms[0]
    return vals[t["id"]], {"terminal": t["id"], "steps": trace}
