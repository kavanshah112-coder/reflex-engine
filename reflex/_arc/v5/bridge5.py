"""V0.5 handoff bridge: the V0.4 v3 EXPRESSION handoff (unchanged gates)
plus the Section-19 dependency CONTRACT lines in the prompt.

The failed V0.4 value handoff is NOT reintroduced (Section 5). All
validation gates are byte-identical to v4.llm_bridge.solve_gap_structured_v3:
expression allowlist, identifier provenance, structural-constant whitelist,
finiteness, magnitude, contradiction; evaluate-then-gate so the no-verify
ablation stays meaningful.

Generation is routed through v4.llm_bridge.generate_json, which llm5
re-points at the active profile server.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401,E402
from v3.ir import KINDS                      # noqa: E402
from v4 import llm_bridge as B4              # noqa: E402
from v4.llm_bridge import (_IDENT, _EXPR_SAFE, _state_json)  # noqa: E402


def _contract_lines(contract):
    if not contract:
        return ""
    lines = []
    cons = contract.get("consumers") or []
    if cons:
        sigs = "; ".join(c["signature"] for c in cons)
        lines.append(
            f"- Downstream use: the solver will feed your quantity into "
            f"{sigs}. Produce the INPUT for that step, not its output.")
    unused = contract.get("unused_available") or []
    if unused:
        lines.append(
            f"- The given quantities {unused} are not consumed by any "
            f"known formula here — the missing computation most likely "
            f"uses them.")
    if contract.get("pair"):
        lines.append(
            f"- Note: the quantity \"{contract['pair']}\" is ALSO unknown "
            f"to the solver; do not use it as a variable.")
    return ("\n".join(lines) + "\n") if lines else ""


def solve_gap_structured_v5(query, state_qs, target_kind, existing_kinds,
                            contract=None):
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
        + _contract_lines(contract) +
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
    out = B4.generate_json(prompt, num_predict=250)
    rec = {"role": "structured_v5", "target_kind": target_kind,
           "prompt_tokens": out["prompt_tokens"],
           "gen_tokens": out["gen_tokens"], "wall_ms": out["wall_ms"],
           "flops_est": out["flops_est"], "raw": out["text"][:500],
           "accepted": False, "value": None, "validation": [],
           "contract_used": bool(contract)}
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
    for q in state_qs:
        state_vals.setdefault(q.kind, q.value)
    idents = {i for i in _IDENT.findall(expr)
              if not re.fullmatch(r"[eE]\d*", i)}
    missing = sorted(i for i in idents if i not in state_vals)
    if missing:
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
    rec["value"] = float(v)
    rec["expr"] = expr[:200]
    rec["method"] = str(d.get("method", ""))[:120]
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
