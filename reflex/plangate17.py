# -*- coding: utf-8 -*-
# origin: new for V1.7 -- the plan gate G-P1..G-P4 (SPEC 4; the V1.3 answer)
"""Decides whether a PLAN (from the composer, a chain reflex, or a
model) may execute at all. V1.3's plan reflexes served 7 and got 7
wrong because their checks verified the plan against the TEXT, never
the QUESTION; this gate exists to close that class:

  G-P1  schema: known ops only, ids unique, DAG (no cycles, no
        forward refs), exactly one final, every node feeds the final.
  G-P2  flow: type discipline along every edge (int slots take int
        producers or integral literals; expr slots take exprs; a
        bool/choice output feeds nothing but the final) and unit
        discipline (a `unit` annotation propagates; `convert` must
        consume its declared `from`).
  G-P3  ask-target: the FINAL node must answer the QUESTION's shape -
        a choice ask ends in `compare`, a truth ask in `is_prime`, a
        requested unit must equal the final's unit (anti-gsm1120: a
        joule plan cannot serve a percent ask).
  G-P4  honesty about numbers: every quantity STATED in the text is
        consumed by the plan (B28 lifted to plan level), and every
        literal the plan uses either comes from the text or is on the
        frozen STRUCTURAL whitelist - a smuggled value is a producer
        answer in disguise (V1.3's ban, enforced structurally).

check(plan, question) -> (ok, transcript). The transcript names every
kill; it rides in the chain certificate.

POSITIVE CONTROL (B24): control_battery() - seven wrong-plan classes
MUST all die; the sound plans MUST pass.
"""
import re

from . import planschema17 as PS
from .gateway16 import CHOICE_ASK, _REQ_UNIT, _UNIT_WORDS, \
    _stated_values


def _req_unit_chain(question):
    """Chain questions name INTERMEDIATE units on the way ('speed in
    m/s ... energy in kJ'); the answer unit is the LAST unit request,
    which rides on the final ask. (V1.6's two-units-ambiguous rule
    stays correct for single-step serving and does not apply here.)"""
    last = None
    for m in _REQ_UNIT.finditer(question):
        last = _UNIT_WORDS[m.group(1).lower()]
    return last

KNOWN_OPS = {"evaluate", "formula", "scale", "convert",
             "derivative_at", "solve_pick", "integrate_def", "limit",
             "sum_finite", "gcd", "lcm", "ncr", "npr", "is_prime",
             "probability", "compare"}

INT_PRODUCERS = {"gcd", "lcm", "ncr", "npr"}
INT_SLOTS = {("gcd", "a"), ("gcd", "b"), ("lcm", "a"), ("lcm", "b"),
             ("ncr", "n"), ("ncr", "r"), ("npr", "n"), ("npr", "r"),
             ("is_prime", "n"), ("sum_finite", "a"),
             ("sum_finite", "b")}
TERMINAL_ONLY = {"compare", "is_prime"}    # bool/choice feed nothing

# frozen structural constants a plan may use without textual warrant
STRUCTURAL = {0.0, 1.0, 2.0, 0.5, 100.0, 1000.0, 9.8, 3.6, 60.0}

BOOL_ASK = re.compile(r"^\s*is\b|\btrue or false\b|\bprime\?", re.I)


def _fail(transcript, gate, why):
    transcript.append({"gate": gate, "kill": why})
    return False


def check(plan, question):
    t = []
    nodes = plan.get("nodes") or []
    # ---------------- G-P1 schema / DAG
    ids = [n.get("id") for n in nodes]
    if not nodes or len(set(ids)) != len(ids):
        return _fail(t, "G-P1", "empty plan or duplicate ids"), t
    seen = set()
    consumers = {i: [] for i in ids}
    for n in nodes:
        if n.get("op") not in KNOWN_OPS:
            return _fail(t, "G-P1", "unknown op %r" % n.get("op")), t
        for slot, ref in PS.refs_in(n):
            if ref not in seen:
                return _fail(t, "G-P1", "forward/unknown ref @%s in "
                             "%s" % (ref, n["id"])), t
            consumers[ref].append((n["op"], slot))
        seen.add(n["id"])
    fin = plan.get("final")
    if fin not in seen:
        return _fail(t, "G-P1", "final %r is not a node" % fin), t
    # reachability: walk back from final
    by_id = {n["id"]: n for n in nodes}
    live, stack = set(), [fin]
    while stack:
        cur = stack.pop()
        if cur in live:
            continue
        live.add(cur)
        stack.extend(r for _s, r in PS.refs_in(by_id[cur]))
    dead = [i for i in ids if i not in live]
    if dead:
        return _fail(t, "G-P1", "nodes never reaching final: %s"
                     % dead), t
    # ---------------- G-P2 type + unit flow
    unit_of = {}
    for n in nodes:
        op = n["op"]
        for slot, ref in PS.refs_in(n):
            src = by_id[ref]["op"]
            if src in TERMINAL_ONLY:
                return _fail(t, "G-P2", "%s output of %s consumed by "
                             "%s" % (src, ref, n["id"])), t
            if (op, slot) in INT_SLOTS and src not in INT_PRODUCERS:
                return _fail(t, "G-P2", "int slot %s.%s fed by "
                             "non-integer producer %s" % (op, slot,
                                                          src)), t
        if op == "convert":
            v = n.get("value")
            if PS.is_ref(v):
                up = v[1:]
                u = unit_of.get(up)
                if u is not None and u != n.get("from"):
                    return _fail(t, "G-P2", "convert from %r but "
                                 "upstream carries %r" % (n.get(
                                     "from"), u)), t
            unit_of[n["id"]] = n.get("to")
        elif "unit" in n:
            unit_of[n["id"]] = n["unit"]
        else:
            # unit propagates through scale; drops elsewhere
            if op == "scale" and PS.is_ref(n.get("value")):
                unit_of[n["id"]] = unit_of.get(n["value"][1:])
    # ---------------- G-P3 ask-target
    final_op = by_id[fin]["op"]
    if CHOICE_ASK.search(question):
        if final_op != "compare":
            return _fail(t, "G-P3", "choice ask; final is %r"
                         % final_op), t
    elif final_op == "compare":
        return _fail(t, "G-P3", "compare final on a value ask"), t
    if BOOL_ASK.search(question) and "prime" in question.lower():
        if final_op != "is_prime":
            return _fail(t, "G-P3", "truth ask; final is %r"
                         % final_op), t
    req = _req_unit_chain(question)
    if req:
        fu = unit_of.get(fin)
        if fu is None or fu != req:
            return _fail(t, "G-P3", "asked in %r; final carries %r"
                         % (req, fu)), t
    # ---------------- G-P4 stated-number honesty
    stated = _stated_values(question)
    lits = []
    for n in nodes:
        for k, v in n.items():
            if k in ("id", "op", "from", "to", "var", "pick", "unit",
                     "order", "expr", "lhs", "rhs"):
                continue
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                lits.append(float(v))
        for k in ("expr", "lhs", "rhs"):
            if k in n and isinstance(n[k], str):
                lits.extend(float(x) for x in re.findall(
                    r"(?<![\w.])(\d+(?:\.\d+)?)", n[k]))
    order_lits = [float(n.get("order", 1)) for n in nodes
                  if n["op"] == "derivative_at"]
    # implicit defaults are consumed literals too ("= 0" in a solve
    # ask is answered by solve_pick's default rhs of 0)
    order_lits += [0.0 for n in nodes
                   if n["op"] == "solve_pick" and "rhs" not in n]
    for s in stated:
        if not any(abs(s - l) < 1e-9 for l in lits + order_lits):
            return _fail(t, "G-P4", "stated quantity %g unused" % s), t
    for l in lits:
        if l in STRUCTURAL or any(abs(l - s) < 1e-9 for s in stated):
            continue
        if float(l).is_integer() and 0 <= l <= 6:
            continue      # small structural ints (orders, indices)
        return _fail(t, "G-P4", "literal %g has no textual warrant "
                     "(value smuggling)" % l), t
    t.append({"gate": "ALL", "pass": True})
    return True, t


# ---------------------------------------------------- positive control
def control_battery():
    q_ke = ("Take the larger root of x^2 - 5x + 6 = 0, multiply it "
            "by 4, and using that as the speed in m/s of a 10 kg "
            "mass, find the kinetic energy in kJ.")
    sound = {"nodes": [
        {"id": "n1", "op": "solve_pick", "lhs": "x**2 - 5*x + 6",
         "pick": "larger"},
        {"id": "n2", "op": "scale", "value": "@n1", "by": 4},
        {"id": "n3", "op": "formula", "expr": "0.5 * m * v**2",
         "m": 10, "v": "@n2", "unit": "J"},
        {"id": "n4", "op": "convert", "value": "@n3", "from": "J",
         "to": "kJ"}], "final": "n4"}
    wrong = [
        ("gsm1120: no conversion, joules serve a kJ ask",
         {"nodes": sound["nodes"][:3], "final": "n3"}, q_ke),
        ("cycle/forward ref",
         {"nodes": [{"id": "n1", "op": "scale", "value": "@n2",
                     "by": 2},
                    {"id": "n2", "op": "scale", "value": "@n1",
                     "by": 3}], "final": "n2"}, q_ke),
        ("unknown op",
         {"nodes": [{"id": "n1", "op": "wish", "value": 3}],
          "final": "n1"}, q_ke),
        ("ignored stated quantity (mass 10 unused)",
         {"nodes": [
             {"id": "n1", "op": "solve_pick",
              "lhs": "x**2 - 5*x + 6", "pick": "larger"},
             {"id": "n2", "op": "scale", "value": "@n1", "by": 4,
              "unit": "kJ"}], "final": "n2"}, q_ke),
        ("smuggled literal 47.3",
         {"nodes": [
             {"id": "n1", "op": "solve_pick",
              "lhs": "x**2 - 5*x + 6", "pick": "larger"},
             {"id": "n2", "op": "scale", "value": "@n1", "by": 4},
             {"id": "n3", "op": "formula", "expr": "0.5 * m * v**2",
              "m": 10, "v": "@n2"},
             {"id": "n4", "op": "scale", "value": "@n3", "by": 47.3,
              "unit": "kJ"}], "final": "n4"}, q_ke),
        ("unit-flow break: convert claims from kg",
         {"nodes": [
             {"id": "n1", "op": "solve_pick",
              "lhs": "x**2 - 5*x + 6", "pick": "larger"},
             {"id": "n2", "op": "scale", "value": "@n1", "by": 4},
             {"id": "n3", "op": "formula", "expr": "0.5 * m * v**2",
              "m": 10, "v": "@n2", "unit": "J"},
             {"id": "n4", "op": "convert", "value": "@n3",
              "from": "kg", "to": "kJ"}], "final": "n4"}, q_ke),
        ("int slot fed by scalar producer",
         {"nodes": [
             {"id": "n1", "op": "formula", "expr": "a/2", "a": 10},
             {"id": "n2", "op": "ncr", "n": "@n1", "r": 2}],
          "final": "n2"},
         "Take half of 10 and compute that many items choose 2."),
        ("compare final on a value ask",
         {"nodes": [
             {"id": "n1", "op": "solve_pick",
              "lhs": "x**2 - 5*x + 6", "pick": "larger"},
             {"id": "n2", "op": "scale", "value": "@n1", "by": 4},
             {"id": "n3", "op": "formula", "expr": "0.5 * m * v**2",
              "m": 10, "v": "@n2", "unit": "kJ"},
             {"id": "n4", "op": "compare", "a": "@n3", "b": 2}],
          "final": "n4"}, q_ke),
    ]
    fails = []
    ok, t = check(sound, q_ke)
    if not ok:
        fails.append(("SOUND KILLED", t[-1]))
    for name, plan, q in wrong:
        ok, t = check(plan, q)
        if ok:
            fails.append(("WRONG PASSED", name))
    return (not fails), fails


if __name__ == "__main__":
    ok, fails = control_battery()
    print("plan gate control battery:", "PASS" if ok else "FAIL",
          "(1 sound + 8 wrong-plan classes)")
    for f in fails:
        print(" ", f)
    raise SystemExit(0 if ok else 1)
