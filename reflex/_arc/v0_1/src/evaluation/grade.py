"""Grading: structured checks first (rubric / numeric / symbolic), LLM-as-judge
only as a secondary metric. Every grade records WHICH method produced it.
"""
import re

import sympy as sp

from src.nodes import sym_engine as se

_NUM_PAT = re.compile(r"(-?\d+(?:,\d{3})*(?:\.\d+)?)(\s*%)?")

# Several held-out surfaces are REVERSE LOOKUPS ("Which law forbids ...?") whose
# correct answer is the concept's NAME, which the content rubric would unfairly
# fail (this would bias grading against the short-answer LLM baseline, flattering
# the reflex system). For these templates a name-rubric is accepted as an
# alternative to the content rubric. Applies identically to every mode.
NAME_RUBRICS = {
    "thermo.first_law": [["first law", "energy conservation",
                          "conservation of energy"]],
    "thermo.second_law": [["second law"]],
    "thermo.zeroth_law": [["zeroth law"]],
    "thermo.entropy_def": [["entropy"]],
    "thermo.enthalpy_def": [["enthalpy"]],
    "thermo.heat_def": [["heat transfer", "heat.", "called heat", "termed heat",
                         "known as heat", "thermal energy"]],
    "thermo.temperature_def": [["kinetic"]],
    "thermo.rev_irrev": [["reversed without", "return to", "restore",
                          "quasi-static", "quasistatic", "entropy"],
                         ["irrevers"]],
    "thermo.entropy_efficiency": [["entropy"],
                                  ["lost", "unavailable", "less work", "reduc",
                                   "waste", "reject", "carnot", "second law"]],
    "thermo.specific_heat": [["specific heat"]],
    "thermo.free_energy": [["gibbs", "free energy"]],
    "thermo.heat_engine_def": [["heat engine"]],
    "thermo.state_vs_path": [["heat"], ["work"], ["path"]],
    "thermo.efficiency_less_100": [["second law", "kelvin"]],
    "mech.newton_first": [["first law", "inertia"]],
    "mech.newton_second": [["second law", "f = ma", "f=ma"]],
    "mech.newton_third": [["third law"]],
    "mech.momentum_def": [["momentum"]],
    "mech.inertia_def": [["inertia", "mass"]],
    "mech.impulse_def": [["impulse"]],
    "mech.work_energy": [["work-energy", "work energy"]],
    "mech.friction": [["friction"]],
    "mech.elastic_inelastic": [["elastic"], ["inelastic", "kinetic"]],
    "mech.cons_energy": [["conservative", "friction", "no friction"],
                         ["energy"]],
    "mech.mass_weight": [["resistance", "inertia", "matter", "amount"],
                         ["force", "gravit", "mg"]],
    "mech.circular": [["centripetal"], ["constant speed", "direction chang"]],
}


def rubric_match(rubric, text):
    """Every group must be matched by at least one entry (substring, case-insens;
    entries containing a backslash are treated as regexes)."""
    low = text.lower()
    for group in rubric:
        hit = False
        for entry in group:
            if "\\" in entry:
                if re.search(entry, low):
                    hit = True
                    break
            elif entry.lower() in low:
                hit = True
                break
        if not hit:
            return False
    return True


def extract_numbers(text):
    out = []
    for m in _NUM_PAT.finditer(text):
        try:
            v = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        out.append((v, bool(m.group(2))))
    return out


def numeric_match(truth, tol, text=None, value=None):
    """value (direct) takes precedence; otherwise ANY number in the text within
    relative tolerance counts (generous to free-text answers; stated in report)."""
    def close(a, b):
        return abs(a - b) <= tol * max(1e-9, abs(b))
    if value is not None:
        return close(value, truth)
    if not text:
        return False
    for v, is_pct in extract_numbers(text):
        if close(v, truth):
            return True
        if is_pct and close(v / 100.0, truth):
            return True
        # fractional truths often reported as bare percentages
        if abs(truth) < 1.5 and v > 1.5 and close(v / 100.0, truth):
            return True
    return False


# --- symbolic extraction from free text -------------------------------------

_LATEX_CLEAN = [
    (re.compile(r"\\\(|\\\)|\\\[|\\\]|\$"), ""),
    (re.compile(r"\\frac\{([^{}]+)\}\{([^{}]+)\}"), r"(\1)/(\2)"),
    (re.compile(r"\\(?:cdot|times)"), "*"),
    (re.compile(r"\\text\{([^{}]*)\}"), r"\1"),
    (re.compile(r"[{}]"), ""),
    (re.compile(r"\\;|\\,|\\ "), " "),
]
_UNICODE_MAP = {"²": "**2", "³": "**3", "½": "(1/2)", "η": "eta", "Δ": "d",
                "×": "*", "·": "*", "−": "-", "√": "sqrt", "θ": "theta",
                "π": "pi", "₀": "0", "₁": "1", "₂": "2", "ᵤ": "u"}


def _clean_math_text(s):
    for pat, rep in _LATEX_CLEAN:
        s = pat.sub(rep, s)
    for k, v in _UNICODE_MAP.items():
        s = s.replace(k, v)
    s = s.replace("^", "**")
    return s


def _candidate_equations(text):
    """Pull 'lhs = rhs' fragments out of prose/markdown."""
    text = _clean_math_text(text)
    cands = []
    for line in text.splitlines():
        line = line.strip().strip("*").strip()
        for m in re.finditer(
                r"([A-Za-z_][A-Za-z_0-9]*(?:\*\*2)?)\s*=\s*"
                r"([0-9A-Za-z_\s\+\-\*/\(\)\.]+)", line):
            lhs, rhs = m.group(1), m.group(2).strip().rstrip(".,;:")
            if rhs:
                cands.append((lhs, rhs))
    return cands


def symbolic_match(target_str, text=None, final_eq_str=None):
    """Check whether the answer contains a relation equivalent to the target.
    Returns (matched, method): method is 'engine_eq' or 'text_parse' or None."""
    ns = se.make_ns(target_str, *( [final_eq_str] if final_eq_str else [] ))
    try:
        target = se.parse_eq(target_str, ns)
    except Exception:
        return False, None
    if final_eq_str:
        try:
            cand = se.parse_eq(final_eq_str, ns)
            if se.relations_equivalent(cand, target) or se.verify_against_target(
                    cand, target_str, ns):
                return True, "engine_eq"
        except Exception:
            pass
        return False, "engine_eq_failed"
    if not text:
        return False, None
    from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                            implicit_multiplication_application)
    trans = standard_transformations + (implicit_multiplication_application,)
    tsyms = {s.name for s in target.free_symbols}
    # Symbol-rendering normalization: variables literally named like 'd2' are
    # often echoed back by an LLM as 'd^2'/'d²' (→ 'd**2' after cleanup). When
    # the target uses such a symbol and the bare letter is NOT itself a target
    # symbol, map the exponent form back to the literal name before parsing.
    renames = []
    for name in tsyms:
        if re.fullmatch(r"([A-Za-z])(\d)", name) and name[0] not in tsyms:
            renames.append((re.compile(rf"\b{name[0]}\s*\*\*\s*{name[1]}"), name))
    for lhs, rhs in _candidate_equations(text):
        try:
            for pat, name in renames:
                lhs = pat.sub(name, lhs)
                rhs = pat.sub(name, rhs)
            local = se.make_ns(target_str, lhs, rhs)
            le = parse_expr(lhs, local_dict=local, transformations=trans,
                            evaluate=True)
            re_ = parse_expr(rhs, local_dict=local, transformations=trans,
                             evaluate=True)
            cand = sp.Eq(le, re_)
            if not isinstance(cand, sp.Eq):
                continue
            csyms = {s.name for s in cand.free_symbols}
            if not (tsyms & csyms):
                continue
            if se.relations_equivalent(cand, target) or se.verify_against_target(
                    cand, target_str, local):
                return True, "text_parse"
        except Exception:
            continue
    return False, "text_parse_failed"


def grade(item, answer_text, numeric_value=None, final_eq_str=None):
    """Primary structured grade. Returns dict {correct, method, detail}."""
    atype = item["answer_type"]
    if answer_text is None and numeric_value is None and final_eq_str is None:
        return {"correct": False, "method": "no_answer", "detail": None}
    if atype == "numeric" and item.get("numeric_answer"):
        na = item["numeric_answer"]
        ok = numeric_match(na["value"], na["tol"], text=answer_text,
                           value=numeric_value)
        return {"correct": ok, "method": "numeric", "detail": na["value"]}
    if atype == "derivation" and item.get("symbolic_answer"):
        tgt = item["symbolic_answer"]["target"]
        ok, method = symbolic_match(tgt, text=answer_text,
                                    final_eq_str=final_eq_str)
        return {"correct": ok, "method": f"symbolic:{method}", "detail": tgt}
    if item.get("rubric"):
        ok = rubric_match(item["rubric"], answer_text or "")
        method = "rubric"
        if not ok and item.get("template_id") in NAME_RUBRICS:
            ok = rubric_match(NAME_RUBRICS[item["template_id"]], answer_text or "")
            method = "rubric_name" if ok else "rubric"
        return {"correct": ok, "method": method, "detail": None}
    return {"correct": False, "method": "ungradable", "detail": None}
