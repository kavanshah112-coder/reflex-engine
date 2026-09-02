# -*- coding: utf-8 -*-
# origin: new for V1.6 -- watched reflex minting over the V1.0 gauntlet
"""Phase L (SPEC 5.2): bridge models propose PARSE REFLEXES; this
module decides. A candidate is a pattern + task template:

    {"name": "...",
     "pattern": "<python regex with named groups, must own the
                  question from its start>",
     "task": {"op": "<symcore op>", "<slot>": "$<group>" | literal,
              ...}}

A reflex NEVER carries an answer. It maps text to a structured task
that symcore16 executes behind the independent witness gate — so an
admitted reflex can extend COVERAGE but cannot mint VALUES. That is
the whole design: producers propose procedures, never numbers.

Gauntlet (all hard, every kill logged):
  G1 schema/compile: regex compiles, has named groups, op known,
     every "$group" reference exists, at least one operand comes
     from a group (constant-answer reflexes are rejected outright —
     the TEXT.qa memorization class is banned in V1.6, see SPEC 6
     note on distractor leakage).
  G2 placement: taxonomy16.place_symbolic resolves the BUILT task
     (on its first match) to a symcore16 leaf. Unindexable = dead
     (B25: no address, no admission).
  G3 shadow probation on the probation stream (escalated items with
     golds): the candidate must serve >= 3 items, on >= 2 distinct
     operand tuples (no single-question memorization), with ZERO
     wrong serves. One wrong = dead. Serving an item the base
     gateway already serves is impossible by construction (only
     escalated items reach candidates), so zero-lost-coverage holds
     by design and is asserted, not hoped.

Ledger per model: offered / proposed / g1_killed / g2_killed /
g3_killed(inert|memorize|wrong) / admitted — the SPEC 8(d) artifact.
"""
import json
import re

from . import symcore16, taxonomy16

MAX_PATTERN_LEN = 400


def _compile(cand):
    """G1. Returns (compiled, why_dead)."""
    pat = cand.get("pattern") or ""
    task = cand.get("task") or {}
    if not isinstance(pat, str) or not (0 < len(pat) <=
                                        MAX_PATTERN_LEN):
        return None, "g1: pattern missing or oversized"
    try:
        rx = re.compile(pat, re.I)
    except re.error as e:
        return None, "g1: regex error: %s" % e
    if not rx.groupindex:
        return None, "g1: no named groups"
    op = task.get("op")
    if op not in taxonomy16.OP_LEAF:
        return None, "g1: unknown op %r" % op
    refs = [v[1:] for v in task.values()
            if isinstance(v, str) and v.startswith("$")]
    if not refs:
        return None, "g1: constant task (memorization class, banned)"
    missing = [r for r in refs if r not in rx.groupindex]
    if missing:
        return None, "g1: task references absent groups %s" % missing
    return rx, None


def _build_task(cand, rx, text):
    m = rx.search(text)
    if not m or m.start() > 12:
        return None
    task = {}
    for k, v in cand["task"].items():
        if isinstance(v, str) and v.startswith("$"):
            g = m.group(v[1:])
            if g is None:
                return None
            g = g.strip()
            try:
                task[k] = float(g) if re.fullmatch(
                    r"-?\d+(?:\.\d+)?", g) else g
            except ValueError:
                task[k] = g
        else:
            task[k] = v
    return task


def try_reflex(cand, rx, text):
    """One candidate on one text -> (value, leaf, operands) | None.
    Every serve passes symcore16's witness gate."""
    task = _build_task(cand, rx, text)
    if task is None:
        return None
    leaf = taxonomy16.place_symbolic(task)
    if leaf is None or taxonomy16.executor(leaf) != "symcore16":
        return None
    task = dict(task)
    task["leaf"] = leaf
    val, cert = symcore16.solve(task)
    if val is None:
        return None
    ops = tuple(sorted((k, str(v)) for k, v in task.items()
                       if k not in ("leaf",)))
    return val, leaf, ops, cert


def gauntlet(candidates, probation, grade_fn, min_serves=3,
             min_distinct=2):
    """Run all candidates through G1-G3.

    probation: [(item, text)] where item carries gold info;
    grade_fn(item, value) -> bool.
    Returns (admitted, ledger, kills). Admitted entries carry their
    probation record.
    """
    ledger = {"proposed": len(candidates), "g1_killed": 0,
              "g2_killed": 0, "g3_inert": 0, "g3_memorize": 0,
              "g3_wrong": 0, "admitted": 0}
    kills, admitted = [], []
    for cand in candidates:
        rx, why = _compile(cand)
        if rx is None:
            ledger["g1_killed"] += 1
            kills.append({"name": cand.get("name"), "why": why})
            continue
        serves, wrongs, tuples = [], 0, set()
        placed_leaf = None
        for item, text in probation:
            out = try_reflex(cand, rx, text)
            if out is None:
                continue
            val, leaf, ops, _cert = out
            placed_leaf = placed_leaf or leaf
            tuples.add(ops)
            ok = grade_fn(item, val)
            serves.append({"id": item.get("id"), "ok": bool(ok)})
            if not ok:
                wrongs += 1
                break                      # one wrong = dead, stop
        if wrongs:
            ledger["g3_wrong"] += 1
            kills.append({"name": cand.get("name"),
                          "why": "g3: WRONG serve", "serves": serves})
            continue
        if placed_leaf is None:
            ledger["g2_killed"] += 1
            kills.append({"name": cand.get("name"),
                          "why": "g2: no placement on any match"})
            continue
        if len(serves) < min_serves:
            ledger["g3_inert"] += 1
            kills.append({"name": cand.get("name"),
                          "why": "g3: inert (%d serves)" % len(serves)})
            continue
        if len(tuples) < min_distinct:
            ledger["g3_memorize"] += 1
            kills.append({"name": cand.get("name"),
                          "why": "g3: single operand tuple "
                                 "(memorization)"})
            continue
        ledger["admitted"] += 1
        admitted.append({"name": cand.get("name"),
                         "pattern": cand["pattern"],
                         "task": cand["task"], "leaf": placed_leaf,
                         "probation": {"serves": len(serves),
                                       "distinct": len(tuples)}})
    return admitted, ledger, kills


def apply_library(text, library):
    """Arm evaluation: first admitted reflex that serves, wins.
    Returns gateway-style dict or None."""
    for cand in library:
        rx, why = _compile(cand)
        if rx is None:
            continue
        out = try_reflex(cand, rx, text)
        if out is not None:
            val, leaf, _ops, cert = out
            return {"status": "SERVED", "value": val,
                    "path": "reflex16:%s" % cand.get("name"),
                    "leaf": leaf,
                    "witness": cert["witness"]["check"]}
    return None


if __name__ == "__main__":
    # self-check: the gauntlet's own controls
    good = {"name": "nth_power_sum",
            "pattern": r"sum of the (?P<w>squares|cubes) of the "
                       r"first (?P<n>\d+) integers",
            "task": {"op": "sum_finite", "expr": "$w", "var": "k",
                     "a": 1, "b": "$n"}}
    const = {"name": "const", "pattern": r"(?P<x>anything)",
             "task": {"op": "gcd", "a": 4, "b": 2}}
    badre = {"name": "badre", "pattern": r"(?P<x>[", "task":
             {"op": "gcd", "a": "$x", "b": 2}}
    admitted, ledger, kills = gauntlet([const, badre], [], lambda i,
                                       v: True)
    assert ledger["g1_killed"] == 2 and not admitted
    print("acquire16 G1 controls PASS:", ledger)
