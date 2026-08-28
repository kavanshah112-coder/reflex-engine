"""LLM cooperation bridge (Sections 4-5, 18-19).

Structured mode: the LLM receives the typed shared state + the query and must
return JSON producing exactly the requested kind. Ollama's format="json" is
used. Every call is logged with reason, state, tokens, and validation outcome.
Unstructured mode (ablation): free text, number extracted by regex.
Validation: schema, kind, finiteness, magnitude sanity, contradiction with
existing state. Downstream compatibility is checked by the caller (resume).
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401

from src.llm import ollama_client as llm     # noqa: E402
from v3.ir import KINDS                      # noqa: E402

BASE = "http://localhost:11434"
MODEL = "llama3.1:latest"


def _state_json(qs):
    return [{"kind": q.kind, "value": round(q.value, 6),
             "unit": q.unit or KINDS.get(q.kind, "")} for q in qs
            if q.source == "query" or not q.kind.startswith("_")]


def generate_json(prompt, num_predict=220, seed=42):
    body = {"model": MODEL, "prompt": prompt, "stream": False,
            "format": "json", "keep_alive": "60m",
            "options": {"num_predict": num_predict, "temperature": 0.0,
                        "seed": seed}}
    t0 = time.perf_counter()
    r = requests.post(f"{BASE}/api/generate", json=body, timeout=600)
    r.raise_for_status()
    d = r.json()
    return {"text": d.get("response", ""),
            "prompt_tokens": d.get("prompt_eval_count", 0),
            "gen_tokens": d.get("eval_count", 0),
            "wall_ms": (time.perf_counter() - t0) * 1000,
            "flops_est": 2.0 * llm.N_PARAMS
            * (d.get("prompt_eval_count", 0) + d.get("eval_count", 0))}


def solve_gap_structured(query, state_qs, target_kind, existing_kinds):
    unit = KINDS.get(target_kind, "")
    prompt = (
        "You are a computational subroutine. A typed solver has partially "
        "processed a problem and needs ONE missing quantity.\n\n"
        f"Problem text: {query}\n\n"
        f"Known quantities (already computed or given): "
        f"{json.dumps(_state_json(state_qs))}\n\n"
        f"Compute the quantity of kind \"{target_kind}\" (unit: "
        f"\"{unit or 'dimensionless'}\").\n"
        "Respond with ONLY this JSON schema:\n"
        '{"status": "solved", "kind": "' + target_kind + '", '
        '"value": <number>, "unit": "...", "method": "<brief formula>", '
        '"assumptions": []}\n'
        'or {"status": "cannot", "reason": "..."}')
    out = generate_json(prompt)
    rec = {"role": "structured", "target_kind": target_kind,
           "prompt_tokens": out["prompt_tokens"],
           "gen_tokens": out["gen_tokens"], "wall_ms": out["wall_ms"],
           "flops_est": out["flops_est"], "raw": out["text"][:400],
           "accepted": False, "value": None, "validation": []}
    try:
        d = json.loads(out["text"])
    except Exception:
        rec["validation"].append("schema:unparseable")
        return rec
    if d.get("status") != "solved":
        rec["validation"].append(f"llm_declined:{d.get('reason', '')[:60]}")
        return rec
    v = d.get("value")
    if not isinstance(v, (int, float)):
        rec["validation"].append("schema:value_not_number")
        return rec
    if d.get("kind") not in (target_kind, None):
        rec["validation"].append("kind_mismatch")
        return rec
    if not (abs(v) < 1e15) or v != v:
        rec["validation"].append("magnitude:insane")
        return rec
    if target_kind in existing_kinds:
        old = existing_kinds[target_kind]
        if abs(old - v) > 0.02 * max(abs(old), 1e-9):
            rec["validation"].append(f"contradiction:{old}vs{v}")
            return rec
    rec["accepted"] = True
    rec["value"] = float(v)
    rec["method"] = str(d.get("method", ""))[:120]
    rec["validation"].append("ok")
    return rec


def solve_gap_structured_v2(query, state_qs, target_kind, existing_kinds):
    """Handoff prompt v2 — designed after v1's VALIDATION-observed failure
    modes (arithmetic slips in one-shot JSON, unit errors, hallucinated
    values for underdetermined gaps; the same modes appeared on test and are
    reported for v1 as an ablation). Changes:
      1. 'work' field FIRST: the model does its arithmetic before committing
         to a value (reasoning space inside JSON).
      2. explicit unit-conversion guidance (J -> kWh etc.).
      3. explicit decline criterion: underdetermined -> status 'cannot'.
      4. typed provenance: 'based_on' must list the input kinds used; any
         kind not present in the shared state rejects the handoff.
    Validation gates of v1 all retained."""
    unit = KINDS.get(target_kind, "")
    known = _state_json(state_qs)
    prompt = (
        "You are a computational subroutine inside a typed solver. The "
        "solver has partially processed a problem and needs ONE missing "
        "quantity.\n\n"
        f"Problem text: {query}\n\n"
        f"Known quantities (already computed or given): "
        f"{json.dumps(known)}\n\n"
        f"Compute the quantity of kind \"{target_kind}\" (unit: "
        f"\"{unit or 'dimensionless'}\").\n"
        "Rules:\n"
        "- Use ONLY the known quantities above and the problem text.\n"
        "- Show the arithmetic step by step in \"work\" BEFORE stating the "
        "value; double-check each multiplication.\n"
        "- Watch units carefully (e.g. 1 kWh = 3.6e6 J; percentages are "
        "already fractions in the known quantities).\n"
        "- \"based_on\" must list exactly the kinds you used.\n"
        "- If the problem does not DETERMINE this quantity from the known "
        "quantities, you MUST decline. Never guess, assume, or invent a "
        "value.\n\n"
        "Respond with ONLY this JSON schema:\n"
        '{"work": "<step-by-step arithmetic>", "status": "solved", '
        '"kind": "' + target_kind + '", "value": <number>, "unit": "...", '
        '"based_on": ["<kind>", ...], "method": "<brief formula>"}\n'
        'or {"work": "<why it is not determined>", "status": "cannot", '
        '"reason": "..."}')
    out = generate_json(prompt, num_predict=500)
    rec = {"role": "structured_v2", "target_kind": target_kind,
           "prompt_tokens": out["prompt_tokens"],
           "gen_tokens": out["gen_tokens"], "wall_ms": out["wall_ms"],
           "flops_est": out["flops_est"], "raw": out["text"][:600],
           "accepted": False, "value": None, "validation": []}
    try:
        d = json.loads(out["text"])
    except Exception:
        rec["validation"].append("schema:unparseable")
        return rec
    if d.get("status") != "solved":
        rec["validation"].append(f"llm_declined:{d.get('reason', '')[:60]}")
        return rec
    v = d.get("value")
    if not isinstance(v, (int, float)):
        rec["validation"].append("schema:value_not_number")
        return rec
    if d.get("kind") not in (target_kind, None):
        rec["validation"].append("kind_mismatch")
        return rec
    if not (abs(v) < 1e15) or v != v:
        rec["validation"].append("magnitude:insane")
        return rec
    state_kinds = {q.kind for q in state_qs}
    based = d.get("based_on")
    if isinstance(based, list) and based:
        missing = [b for b in based if isinstance(b, str)
                   and b not in state_kinds and b != target_kind]
        if missing:
            rec["validation"].append(
                f"provenance:unknown_input:{','.join(missing[:3])}")
            return rec
    if target_kind in existing_kinds:
        old = existing_kinds[target_kind]
        if abs(old - v) > 0.02 * max(abs(old), 1e-9):
            rec["validation"].append(f"contradiction:{old}vs{v}")
            return rec
    rec["accepted"] = True
    rec["value"] = float(v)
    rec["method"] = str(d.get("method", ""))[:120]
    rec["work"] = str(d.get("work", ""))[:300]
    rec["validation"].append("ok")
    return rec


_IDENT = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")
_EXPR_SAFE = re.compile(r"^[\w\s+\-*/().]+$")


def solve_gap_structured_v3(query, state_qs, target_kind, existing_kinds):
    """Handoff v3 — EXPRESSION handoff (validation-designed after v2):
    v1/v2 showed llama3.1-8B states the correct METHOD almost every time but
    commits arithmetically wrong VALUES (validation examples: computed
    '8/3 L' in its work then answered 8.0; dropped 3 orders of magnitude).
    So the LLM now returns a pure arithmetic EXPRESSION over the typed state
    variable names and the DETERMINISTIC EXECUTOR evaluates it — 'LLM
    proposes, typed system executes', the architecture's own thesis applied
    at handoff time.

    Safety: expression allowlist (arithmetic chars only), every identifier
    must be a kind present in the shared state (a hallucinated input kind
    rejects the handoff — this is what kills invented values on
    underdetermined gaps), finiteness/magnitude/contradiction gates
    retained."""
    unit = KINDS.get(target_kind, "")
    known = _state_json(state_qs)
    kinds_avail = sorted({q.kind for q in state_qs})
    prompt = (
        "You are a formula generator inside a typed solver. The solver has "
        "partially processed a problem and needs ONE missing quantity. The "
        "solver will evaluate your formula EXACTLY — do NOT compute the "
        "value yourself.\n\n"
        f"Problem text: {query}\n\n"
        f"Known quantities (name: value unit): {json.dumps(known)}\n\n"
        f"Give a formula for the quantity of kind \"{target_kind}\" (unit: "
        f"\"{unit or 'dimensionless'}\").\n"
        "Rules:\n"
        f"- The formula may use ONLY these variable names: {kinds_avail} "
        "plus structural constants (1, 2, 0.5, unit conversions like "
        "3.6e6) and + - * / ( ) and ** for powers.\n"
        f"- The formula must compute \"{target_kind}\" ITSELF, not the "
        "problem's final answer.\n"
        "- Rates are already fractions (7% is 0.07). Watch units "
        "(1 kWh = 3.6e6 J).\n"
        "- Every problem-specific number must come from the variables, "
        "NEVER appear as a literal in the formula.\n"
        "- If the known quantities do not DETERMINE this value, decline. "
        "Never invent numbers or rates for missing information.\n\n"
        "Respond with ONLY this JSON schema:\n"
        '{"status": "solved", "expr": "<arithmetic expression>", '
        '"method": "<brief description>"}\n'
        'or {"status": "cannot", "reason": "..."}')
    out = generate_json(prompt, num_predict=250)
    rec = {"role": "structured_v3", "target_kind": target_kind,
           "prompt_tokens": out["prompt_tokens"],
           "gen_tokens": out["gen_tokens"], "wall_ms": out["wall_ms"],
           "flops_est": out["flops_est"], "raw": out["text"][:500],
           "accepted": False, "value": None, "validation": []}
    try:
        d = json.loads(out["text"])
    except Exception:
        rec["validation"].append("schema:unparseable")
        return rec
    if d.get("status") != "solved":
        rec["validation"].append(f"llm_declined:{d.get('reason', '')[:60]}")
        return rec
    expr = str(d.get("expr", "")).replace("^", "**")
    if not expr or not _EXPR_SAFE.match(expr.replace("**", "")):
        rec["validation"].append("expr:unsafe_or_empty")
        return rec
    state_vals = {}
    for q in state_qs:                      # first value of each kind
        state_vals.setdefault(q.kind, q.value)
    idents = {i for i in _IDENT.findall(expr)
              if not re.fullmatch(r"[eE]\d*", i)}  # 3.6e6 sci literals
    missing = sorted(i for i in idents if i not in state_vals)
    if missing:
        # cannot even evaluate — not a verification gate, an impossibility
        rec["validation"].append(
            f"provenance:unknown_input:{','.join(missing[:3])}")
        return rec
    try:
        v = eval(expr, {"__builtins__": {}},
                 {k: state_vals[k] for k in idents})
    except Exception as e:
        rec["validation"].append(f"expr:eval_error:{str(e)[:40]}")
        return rec
    if not isinstance(v, (int, float)) or v != v:
        rec["validation"].append("expr:non_numeric")
        return rec
    # the value exists from here on (the no-verify ablation integrates it
    # regardless); the gates below decide 'accepted' for the default mode
    rec["value"] = float(v)
    rec["expr"] = expr[:200]
    rec["method"] = str(d.get("method", ""))[:120]
    # constant gate: structural constants (identities, unit conversions,
    # physical g) are allowed; FREE numeric literals are how a model
    # smuggles invented values past provenance — reject them
    lits = [float(x) for x in re.findall(
        r"(?<![\w.])\d+(?:\.\d+)?(?:[eE]\d+)?", expr)]
    allowed = {0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 10.0, 12.0, 60.0, 100.0,
               1000.0, 3600.0, 3.6, 3.6e6, 9.8, 9.81}
    bad = [x for x in lits if x not in allowed]
    if bad:
        rec["validation"].append(
            f"constant:invented:{','.join(str(b) for b in bad[:3])}")
        return rec
    if not abs(v) < 1e15:
        rec["validation"].append("magnitude:insane")
        return rec
    if target_kind in existing_kinds:
        old = existing_kinds[target_kind]
        if abs(old - v) > 0.02 * max(abs(old), 1e-9):
            rec["validation"].append(f"contradiction:{old}vs{v}")
            return rec
    rec["accepted"] = True
    rec["validation"].append("ok")
    return rec


_NUMS = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?")


def solve_gap_unstructured(query, state_qs, target_kind, existing_kinds):
    unit = KINDS.get(target_kind, "")
    prompt = (f"Problem: {query}\n\nAlready known: "
              + ", ".join(f"{q.kind}={q.value:g}{q.unit}"
                          for q in state_qs)
              + f"\n\nWhat is the {target_kind.replace('_', ' ')}"
              + (f" in {unit}" if unit else "") + "? Answer briefly.")
    out = llm.generate(prompt, num_predict=150)
    rec = {"role": "unstructured", "target_kind": target_kind,
           "prompt_tokens": out["prompt_tokens"],
           "gen_tokens": out["gen_tokens"], "wall_ms": out["wall_ms"],
           "flops_est": out["flops_est"], "raw": out["text"][:400],
           "accepted": False, "value": None, "validation": []}
    nums = [float(x.replace(",", "")) for x in _NUMS.findall(out["text"])]
    if not nums:
        rec["validation"].append("no_number_found")
        return rec
    rec["accepted"] = True
    rec["value"] = nums[-1]   # convention: final number is the answer
    rec["validation"].append("extracted_last_number")
    return rec
