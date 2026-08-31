# -*- coding: utf-8 -*-
# origin: new for V1.3 — W3/W4 plan IR, checks, execution
"""The typed plan: what a model is allowed to hand the engine, and
everything the engine does to it before trusting it.

A plan is quantities + an ordered DAG of arithmetic steps + a target
+ an explicit list of dismissed quantities. It contains NO computed
values — the engine evaluates every step itself (V0.4: value handoff
66.1% harmful vs expression handoff 84.3%; V0.8: raw-value interfaces
36-39% vs typed 84%+).

Checks, in the order they run (V1_3_SPEC §6):
  AGREEMENT    two independent parses must describe the same plan
  ROUND-TRIP   the plan's quantities/target must match the text
  CONSUMPTION  every number in the text is used or explicitly
               dismissed with a reason
  SCOPE        the plan ends at the target kind, and any scope the
               ask names is represented by a step
  DIMENSIONAL  each step type-checks where kinds are known
"""
import re

OPS = {"add": lambda a, b: a + b,
       "sub": lambda a, b: a - b,
       "mul": lambda a, b: a * b,
       "div": lambda a, b: (a / b) if b else None}

NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
# scope words the ask may name; a plan claiming one should show it
SCOPE_WORDS = re.compile(
    r"\b(per|each|every|daily|weekly|monthly|yearly|annually|total|"
    r"altogether|combined|difference|saved?|savings|more than|less "
    r"than|fewer|remaining|left|change)\b", re.I)


# --------------------------------------------------------- structure
def validate(ir):
    """Structural validation. -> (ok, reason)."""
    if not isinstance(ir, dict):
        return False, "not_an_object"
    qs = ir.get("quantities")
    steps = ir.get("plan")
    tgt = ir.get("target")
    if not isinstance(qs, list) or not qs:
        return False, "no_quantities"
    if not isinstance(steps, list) or not steps:
        return False, "no_plan"
    if not isinstance(tgt, dict) or not tgt.get("kind"):
        return False, "no_target"
    ids = set()
    for q in qs:
        if not isinstance(q, dict) or "id" not in q:
            return False, "quantity_missing_id"
        if "value" not in q or not isinstance(
                q["value"], (int, float)):
            return False, "quantity_missing_value"
        if q["id"] in ids:
            return False, f"duplicate_id:{q['id']}"
        ids.add(q["id"])
    for i, s in enumerate(steps):
        if not isinstance(s, dict):
            return False, f"step{i}_not_object"
        if s.get("op") not in OPS:
            return False, f"step{i}_bad_op:{s.get('op')}"
        args = s.get("args")
        if not isinstance(args, list) or len(args) != 2:
            return False, f"step{i}_bad_args"
        for a in args:
            if a not in ids:
                return False, f"step{i}_unknown_ref:{a}"
        out = s.get("out")
        if not out or out in ids:
            return False, f"step{i}_bad_out"
        ids.add(out)
    # a plan whose last step feeds nothing is the answer
    return True, "ok"


def execute(ir):
    """Deterministic evaluation. -> (value, trace) or (None, reason).
    No model-supplied number is ever used as a result."""
    env = {}
    for q in ir["quantities"]:
        env[q["id"]] = float(q["value"])
    trace = []
    last = None
    for s in ir["plan"]:
        a, b = env.get(s["args"][0]), env.get(s["args"][1])
        if a is None or b is None:
            return None, f"unbound:{s['args']}"
        try:
            v = OPS[s["op"]](a, b)
        except Exception as e:
            return None, f"exec_error:{type(e).__name__}"
        if v is None:
            return None, "div_by_zero"
        env[s["out"]] = v
        trace.append({"step": s["out"], "op": s["op"],
                      "args": s["args"], "value": v})
        last = v
    return last, trace


# ------------------------------------------------------------ checks
def _word_numbers(text):
    """Spelled-out numbers ("ninety-one hotdogs", "three more stops").
    V1.3: real word problems are full of these. Without them the
    round-trip and consumption checks reject any plan that correctly
    writes 'ninety-one' as 91, which silently made an entire class of
    problem unsolvable rather than merely hard."""
    try:
        import sys
        from pathlib import Path as _P
        arc = _P(__file__).resolve().parent / "_arc"
        if str(arc) not in sys.path:
            sys.path.insert(0, str(arc))
        from v10.nlpw10 import WORDNUM_RE
        from v9.sqr9 import words_to_number
    except Exception:
        return []
    out = []
    for m in WORDNUM_RE.finditer(text):
        v = words_to_number(m.group(1).lower().replace("-", " "))
        if v is not None:
            out.append(float(v))
    return out


def _nums_in_text(text, include_words=True):
    """`include_words` is deliberately asymmetric between the two
    checks that call this, and the asymmetry is the point (B12).

    The word-number extractor is a RECOGNISER, not a quantity
    detector: it reads "the third team" as 0.333 and "One stack" as
    1, because those spans really do denote numbers in some contexts.
    That is exactly what ROUND-TRIP wants -- it asks whether a value
    the model wrote can be JUSTIFIED by the text, so a permissive
    reading only ever admits honest parses.

    CONSUMPTION asks the opposite question: is there a number here the
    plan FAILED to account for. Feeding it the same permissive
    extractor makes it demand that "one" in "one of his robot sets" be
    used or dismissed, and correct plans start failing on phantoms.
    So consumption sees digits only.
    """
    out = []
    for m in NUM_RE.finditer(text):
        try:
            out.append(float(m.group(0).replace(",", "")))
        except ValueError:
            continue
    return out + _word_numbers(text) if include_words else out


def check_roundtrip(ir, text):
    """Every quantity the plan claims must actually appear in the
    text, with its unit token nearby when one is claimed."""
    nums = _nums_in_text(text)
    bad = []
    for q in ir["quantities"]:
        v = float(q["value"])
        if not any(abs(v - n) < 1e-9 for n in nums):
            bad.append({"id": q["id"], "value": v,
                        "why": "value_not_in_text"})
            continue
        u = (q.get("unit") or "").strip().lower()
        if u and len(u) > 1 and u not in text.lower():
            bad.append({"id": q["id"], "unit": u,
                        "why": "unit_not_in_text"})
    return (not bad), bad


def check_consumption(ir, text):
    """Every number in the text is used by a step or explicitly
    dismissed. gsm0403 answered while '30 days' sat unused."""
    nums = _nums_in_text(text, include_words=False)   # B12
    claimed = {float(q["value"]) for q in ir["quantities"]}
    dismissed = {float(d["value"]) for d in (ir.get("dismissed") or [])
                 if isinstance(d, dict) and "value" in d}
    used_ids = {a for s in ir["plan"] for a in s["args"]}
    used_vals = {float(q["value"]) for q in ir["quantities"]
                 if q["id"] in used_ids}
    orphans = []
    for n in nums:
        if any(abs(n - c) < 1e-9 for c in used_vals):
            continue
        if any(abs(n - c) < 1e-9 for c in dismissed):
            continue
        # a number that is part of a year/ordinal/etc. still counts:
        # the parser must say why it is not needed
        orphans.append(n)

    # B16. The loop above walks numbers found in the TEXT, so after
    # B12 restricted it to digits it goes silent on a problem written
    # entirely in words -- and a plan may then declare a quantity,
    # never use it, and never dismiss it, with nothing objecting.
    # That is how "Kaleb won eight tickets and seven tickets, candy
    # costs five tickets each, how many could he buy?" certified as
    # add(8,7) = 15 with q3 = 5 sitting unused. Truth 3.
    #
    # This clause asks the question plan-internally instead, where no
    # text extraction can weaken it: a quantity the parser bothered to
    # DECLARE must be used by a step or explicitly dismissed. It
    # restores what consumption was always meant to enforce.
    for q in ir["quantities"]:
        if q["id"] in used_ids:
            continue
        v = float(q["value"])
        if any(abs(v - c) < 1e-9 for c in dismissed):
            continue
        orphans.append({"id": q["id"], "value": v,
                        "why": "declared_but_never_used"})
    return (not orphans), orphans


def check_scope(ir, text):
    """The plan must END at the target, and if the ask names a scope
    word the plan must contain more than one step (a scoped answer is
    never a single lookup)."""
    steps = ir["plan"]
    outs = {s["out"] for s in steps}
    consumed = {a for s in steps for a in s["args"]}
    terminals = outs - consumed
    if len(terminals) != 1:
        return False, {"why": "plan_does_not_converge",
                       "terminals": sorted(terminals)}
    if steps[-1]["out"] not in terminals:
        return False, {"why": "last_step_is_not_the_answer"}
    ask = text.split("?")[0].split(".")[-1] if "?" in text else text
    if SCOPE_WORDS.search(ask) and len(steps) < 1:
        return False, {"why": "scoped_ask_without_steps"}
    return True, {}


def check_dimensional(ir, kinds):
    """Type-check each step where kinds are known. Returns
    (ok, detail); detail records how much was actually verifiable —
    on real language many kinds fall outside the pack, and an
    unverifiable plan must be reported as such, never as verified."""
    kind_of = {q["id"]: q.get("kind") for q in ir["quantities"]}
    known = checked = 0
    total = 0
    for s in ir["plan"]:
        total += 1
        ka = kind_of.get(s["args"][0])
        kb = kind_of.get(s["args"][1])
        if ka in kinds and kb in kinds:
            known += 1
            da, db = kinds[ka][0], kinds[kb][0]
            if s["op"] in ("add", "sub") and da != db:
                return False, {"why": "add_sub_dimension_mismatch",
                               "step": s["out"],
                               "kinds": [ka, kb]}
            checked += 1
        kind_of[s["out"]] = None      # derived kinds are untyped here
    return True, {"steps": total, "dimensionally_verifiable": known,
                  "verified": checked}


def _symbolic(ir):
    """Reduce the plan symbolically over its input ids. Returns a
    canonical string, plus the set of input ids that actually affect
    the result."""
    expr = {q["id"]: (q["id"],) for q in ir["quantities"]}
    for s in ir["plan"]:
        a, b = expr.get(s["args"][0]), expr.get(s["args"][1])
        if a is None or b is None:
            return None, set()
        expr[s["out"]] = (s["op"], a, b)
    outs = {s["out"] for s in ir["plan"]}
    consumed = {a for s in ir["plan"] for a in s["args"]}
    term = list(outs - consumed) or [ir["plan"][-1]["out"]]
    root = expr[term[0]]

    def leaves(e):
        if isinstance(e, tuple) and len(e) == 1:
            return {e[0]}
        if isinstance(e, tuple) and len(e) == 3:
            return leaves(e[1]) | leaves(e[2])
        return set()
    return root, leaves(root)


def check_nondegenerate(ir, value):
    """V1.3 B4: reject plans that do arithmetic and arrive back at an
    input. Two failure shapes seen in the first real-language smoke,
    both certified and both wrong:
      (25-35)+35   -> 25      "Adam ran 25 more than Katie"
      (2584-704)+704 -> 2584  "tuition is $704 more than room+board"
    The model builds a plausible-looking multi-step plan that is
    algebraically the identity, and every other check passes: the
    values are in the text, all numbers are consumed, the plan
    converges, and the kinds are too generic to type-check.
    """
    steps = ir.get("plan") or []
    if len(steps) < 2:
        return True, {}
    vals = {q["id"]: float(q["value"]) for q in ir["quantities"]}
    if value is not None:
        for qid, v in vals.items():
            if abs(v - value) < 1e-9:
                return False, {"why": "answer_equals_an_input",
                               "input": qid, "value": v}
    root, used = _symbolic(ir)
    if root is not None and isinstance(root, tuple) and             len(root) == 1:
        return False, {"why": "plan_reduces_to_an_input"}
    if len(used) < 2:
        return False, {"why": "plan_depends_on_one_input_only",
                       "inputs_used": sorted(used)}
    return True, {}


def agreement(ir_a, ir_b):
    """Two parses agree if they claim the same quantity values, the
    same target kind, and the same multiset of operations."""
    if ir_a is None or ir_b is None:
        return False, "one_parse_missing"
    va = sorted(round(float(q["value"]), 6) for q in
                ir_a.get("quantities", []))
    vb = sorted(round(float(q["value"]), 6) for q in
                ir_b.get("quantities", []))
    if va != vb:
        return False, "quantities_differ"
    ta = (ir_a.get("target") or {}).get("kind")
    tb = (ir_b.get("target") or {}).get("kind")
    if ta != tb:
        return False, f"target_differs:{ta}|{tb}"
    oa = sorted(s["op"] for s in ir_a.get("plan", []))
    ob = sorted(s["op"] for s in ir_b.get("plan", []))
    if oa != ob:
        return False, "operations_differ"
    return True, "ok"


def verify(ir_a, ir_b, text, kinds):
    """Run all five checks in order. -> (ok, report)."""
    rep = {}
    ok, why = agreement(ir_a, ir_b)
    rep["agreement"] = {"ok": ok, "why": why}
    if not ok:
        return False, rep
    ir = ir_a
    ok, why = validate(ir)
    rep["structure"] = {"ok": ok, "why": why}
    if not ok:
        return False, rep
    ok, bad = check_roundtrip(ir, text)
    rep["roundtrip"] = {"ok": ok, "bad": bad}
    if not ok:
        return False, rep
    ok, orphans = check_consumption(ir, text)
    rep["consumption"] = {"ok": ok, "orphans": orphans}
    if not ok:
        return False, rep
    ok, detail = check_scope(ir, text)
    rep["scope"] = {"ok": ok, **detail}
    if not ok:
        return False, rep
    ok, detail = check_dimensional(ir, kinds)
    rep["dimensional"] = {"ok": ok, **detail}
    if not ok:
        return False, rep
    # B4: non-degeneracy runs last because it needs the executed
    # value; a plan that computes its way back to an input is not an
    # answer, however well-formed it looks.
    value, _trace = execute(ir)
    ok, detail = check_nondegenerate(ir, value)
    rep["nondegenerate"] = {"ok": ok, **detail}
    if not ok:
        return False, rep
    return True, rep
