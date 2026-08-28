# -*- coding: utf-8 -*-
"""V0.8 indexed LLM step solver + full-query solver (spec Sections
16-19, 22, 26-27).

Index levels (ablation, Section 22):
  I0  no index: query text + required kind        -> RAW NUMBER
  I1  + QUERY_INDEX block                         -> RAW NUMBER
  I2  + PATH_INDEX block (no I1, no typed state)  -> RAW NUMBER
  I3  I1 + I2                                     -> RAW NUMBER
  I4  I3 + typed CURRENT_STATE                    -> TYPED EXPRESSION
  I5  I4 + handover contract (production mode)    -> TYPED EXPRESSION

I0-I3 are deliberately raw-value handoffs: V0.4 proved value handoff
harmful; the ablation measures whether indexing alone mitigates it and
whether typed state (I4+) is where safety comes from. Production = I5.

All expression validation gates are the frozen V0.4/V0.5 gates
(v4.llm_bridge / v5.bridge5), plus V0.8 provenance checks.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401,E402
from v3.ir import KINDS                              # noqa: E402
from v4 import llm_bridge as B4                      # noqa: E402
from v4.llm_bridge import _IDENT, _EXPR_SAFE         # noqa: E402

NUM_RE = re.compile(r"-?\d+(?:\.\d+)?(?:[eE]-?\d+)?")


def _qindex_block(ctx):
    return (f"QUERY_INDEX: {ctx['query_id']}\n"
            f"ORIGINAL_QUERY: {ctx['query']}\n"
            f"FINAL_OBJECTIVE: {ctx['target']}\n"
            f"RECOGNIZED_INPUTS: {ctx.get('input_kinds', [])}\n")


def _pindex_block(ctx):
    lines = [f"PATH_INDEX: {ctx.get('path_id', '?')}",
             f"CURRENT_STEP: {ctx['step_id']} / {ctx['n_steps']}"]
    for c in ctx.get("completed", []):
        lines.append(f"COMPLETED: STEP {c['step']} -> {c['cap']} -> "
                     f"{c['by']} OK")
    lines.append(f"THIS_STEP: STEP {ctx['step_id']} -> LLM -> produce "
                 f"kind \"{ctx['need_kind']}\"")
    nxt = ctx.get("next_caps") or []
    if nxt:
        lines.append(f"NEXT: {'; '.join(nxt)} (Reflex)")
    return "\n".join(lines) + "\n"


def _state_block(ctx):
    lines = ["CURRENT_STATE (validated typed values):"]
    for s in ctx.get("state", []):
        lines.append(f"  {s['kind']} = {s['value']:.10g} "
                     f"{KINDS.get(s['kind'], '')} "
                     f"[{s.get('provenance', 'query')}]")
    return "\n".join(lines) + "\n"


def step_prompt(ilevel, ctx):
    """Build the step-solve prompt for index level I0..I5."""
    need = ctx["need_kind"]
    unit = KINDS.get(need, "") or "dimensionless"
    head = ("You are one step inside an indexed multi-step solver. "
            "Solve ONLY the assigned step — not the whole problem.\n\n")
    body = ""
    if ilevel == 0:
        head = ("You are helping solve a problem.\n\n")
        body = f"Problem: {ctx['query']}\n\n"
    if ilevel in (1, 3, 4, 5):
        body += _qindex_block(ctx) + "\n"
    if ilevel in (2, 3, 4, 5):
        body += _pindex_block(ctx) + "\n"
    if ilevel == 2:
        body = f"Problem: {ctx['query']}\n\n" + body
    if ilevel >= 4:
        body += _state_block(ctx) + "\n"
    if ilevel <= 3:
        if ilevel != 0 and ilevel != 2:
            pass
        ask = (f"Compute the value of the quantity of kind \"{need}\" "
               f"(unit: {unit}) needed at this point.\n"
               "Respond with ONLY this JSON:\n"
               '{"query_id": "<id>", "step_id": <n>, '
               f'"output_kind": "{need}", "value": <number>}}\n'
               "Use query_id/step_id exactly as given (or \"none\" if "
               "not given).")
        return head + body + ask, "value"
    contract = ""
    if ilevel == 5:
        nxt = ctx.get("next_caps") or []
        if nxt:
            contract += ("- Your output feeds the next Reflex step: "
                         + "; ".join(nxt) +
                         ". Produce its INPUT, not its output.\n")
        contract += ("- If the state does not DETERMINE this value, "
                     "return {\"status\": \"cannot\"} instead. Never "
                     "invent numbers.\n")
    varnames = sorted({s["kind"] for s in ctx.get("state", [])})
    ask = (
        f"Give a FORMULA for the quantity of kind \"{need}\" (unit: "
        f"{unit}).\n"
        "Rules:\n"
        f"- Use ONLY these variable names: {varnames} plus structural "
        "constants (1, 2, 0.5, 9.8, 3.6e6) and + - * / ( ) **.\n"
        "- The solver evaluates the formula EXACTLY; do not compute the "
        "value yourself.\n"
        "- Problem-specific numbers must come from variables, never "
        "appear as literals.\n" + contract +
        "Respond with ONLY this JSON:\n"
        '{"query_id": "<id>", "path_id": "<id>", "step_id": <n>, '
        f'"output_kind": "{need}", "expression": "<formula>", '
        '"inputs_used": ["<var>", ...]}\n'
        'or {"status": "cannot", "reason": "..."}')
    return head + body + ask, "expr"


def route_prompt(ctx):
    """Section 20: ask the LLM which step to execute next."""
    body = _qindex_block(ctx) + "\n" + _pindex_block(ctx) + "\n" + \
        _state_block(ctx) + "\n"
    opts = ctx["route_options"]
    return (
        "You are the routing supervisor of an indexed multi-step "
        "solver.\n\n" + body +
        f"Which capability should execute NEXT? Options: {opts}\n"
        "Answer the single best option. A capability is executable only "
        "if all its input kinds are in CURRENT_STATE.\n"
        "Respond with ONLY this JSON: "
        '{"next": "<capability name>", "step_id": <n>}')


def full_prompt(query):
    """Condition A: model solves the entire query, numeric answer."""
    return (
        "Solve this problem. Think briefly, then give the final "
        "numeric answer.\n\n"
        f"Problem: {query}\n\n"
        "Respond with ONLY this JSON on the last line:\n"
        '{"answer": <number>, "unit": "<unit>"}')


def _find_json(text):
    for line in reversed([l for l in text.splitlines() if l.strip()]):
        try:
            return json.loads(line)
        except Exception:
            continue
    m = re.search(r"\{[^{}]*\}", text, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def call_step(ilevel, ctx, num_predict=260):
    prompt, mode = step_prompt(ilevel, ctx)
    out = B4.generate_json(prompt, num_predict=num_predict)
    rec = {"role": f"step_I{ilevel}", "mode": mode,
           "need_kind": ctx["need_kind"],
           "prompt_tokens": out.get("prompt_tokens"),
           "gen_tokens": out.get("gen_tokens"),
           "wall_ms": out.get("wall_ms"), "raw": out["text"][:400],
           "chars_out": len(out["text"]),
           "accepted": False, "value": None, "validation": []}
    return validate_step_text(out["text"], ilevel, ctx, mode, rec)


def validate_step_text(text, ilevel, ctx, mode, rec=None):
    """Validation + deterministic evaluation of a step response.
    Separated so the Section-27 fault suite can drive it with synthetic
    responses. All gates identical for live and synthetic input."""
    if rec is None:
        rec = {"role": f"step_I{ilevel}", "mode": mode,
               "need_kind": ctx["need_kind"], "raw": text[:400],
               "chars_out": len(text), "accepted": False,
               "value": None, "validation": []}
    d = _find_json(text)
    if d is None or not isinstance(d, dict):
        rec["validation"].append("schema:unparseable")
        return rec
    if d.get("status") == "cannot":
        rec["validation"].append("llm_declined")
        rec["declined"] = True
        return rec
    # provenance checks (Sections 17-18): ids must echo the index
    if ilevel >= 1:
        want_q = ctx.get("query_id")
        got_q = d.get("query_id")
        if want_q and got_q not in (want_q, "none", None):
            rec["validation"].append("provenance:query_id_mismatch")
            return rec
        got_s = d.get("step_id")
        if got_s is not None and ctx.get("step_id") is not None and \
                str(got_s) != str(ctx["step_id"]):
            rec["validation"].append("provenance:step_id_mismatch")
            return rec
    if d.get("output_kind") not in (None, ctx["need_kind"]):
        rec["validation"].append("kind:wrong_output_kind")
        return rec
    if mode == "value":
        v = d.get("value")
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            rec["validation"].append("value:not_numeric")
            return rec
        rec["accepted"] = True
        rec["value"] = float(v)
        rec["handoff_kind"] = "raw_value"
        return rec
    # expression mode: frozen V0.4/V0.5 gates
    expr = str(d.get("expression", d.get("expr", ""))).replace("^", "**")
    if not expr or not _EXPR_SAFE.match(expr.replace("**", "")):
        rec["validation"].append("expr:unsafe_or_empty")
        return rec
    state_vals = {}
    for s in ctx.get("state", []):
        state_vals.setdefault(s["kind"], s["value"])
    idents = {i for i in _IDENT.findall(expr)
              if not re.fullmatch(r"[eE]\d*", i)}
    missing = sorted(i for i in idents if i not in state_vals)
    if missing:
        rec["validation"].append(f"expr:unknown_idents:{missing[:3]}")
        return rec
    if not idents:
        rec["validation"].append("expr:no_variables")
        return rec
    # literal check: any problem-specific literal >= 10 is suspicious
    lits = [float(x) for x in NUM_RE.findall(
        re.sub(r"[a-zA-Z_][a-zA-Z_0-9]*", "", expr))]
    bad = [x for x in lits if x not in (1.0, 2.0, 0.5, 9.8, 100.0,
                                        3.6e6, 3600.0, 60.0, 1000.0)
           and abs(x) > 4]
    if bad:
        rec["validation"].append(f"expr:invented_literal:{bad[:2]}")
        return rec
    try:
        v = eval(expr, {"__builtins__": {}, "math": math}, dict(state_vals))
    except Exception as e:
        rec["validation"].append(f"expr:eval_error:{e}")
        return rec
    if not isinstance(v, (int, float)) or not math.isfinite(v):
        rec["validation"].append("expr:non_finite")
        return rec
    rec["accepted"] = True
    rec["value"] = float(v)
    rec["expression"] = expr
    rec["inputs_used"] = sorted(idents)
    rec["handoff_kind"] = "typed_expression"
    return rec


def call_route(ctx, num_predict=80):
    prompt = route_prompt(ctx)
    out = B4.generate_json(prompt, num_predict=num_predict)
    d = _find_json(out["text"]) or {}
    return {"role": "route", "raw": out["text"][:200],
            "chars_out": len(out["text"]),
            "prompt_tokens": out.get("prompt_tokens"),
            "gen_tokens": out.get("gen_tokens"),
            "next": d.get("next"), "wall_ms": out.get("wall_ms")}


def call_full(query, num_predict=380):
    out = B4.generate_json(full_prompt(query), num_predict=num_predict)
    d = _find_json(out["text"]) or {}
    v = d.get("answer")
    ok = isinstance(v, (int, float)) and math.isfinite(v)
    return {"role": "full", "raw": out["text"][:400],
            "chars_out": len(out["text"]),
            "prompt_tokens": out.get("prompt_tokens"),
            "gen_tokens": out.get("gen_tokens"),
            "wall_ms": out.get("wall_ms"),
            "value": float(v) if ok else None, "accepted": bool(ok)}
