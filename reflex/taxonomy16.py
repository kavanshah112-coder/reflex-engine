# -*- coding: utf-8 -*-
# origin: new for V1.6 -- runtime API over the frozen taxonomy (SPEC 5.1)
"""Loads taxonomy.json (frozen at v1.6-plan) and answers the three
questions the pipeline asks of it:

  * is this path a real leaf, and which executor owns it?
  * which leaf does an existing capability live at?
  * OP_LEAF: which leaf does a structured symcore op certify under?

OP_LEAF is the evidence-checkable placement rule for the symbolic
side: the leaf is a function of the task's op and operands (e.g. a
differentiate task with order 2 is second_derivative), never of what
any producer calls it (B25: names are not evidence).

The module never mutates the taxonomy. Reflex indexing during
acquisition uses place_symbolic()/capability leaf lookups and REFUSES
(returns None) when no rule applies -- an unindexable reflex is
rejected by acquire16, whatever its probation record.
"""
import json
from pathlib import Path

_DOC = None
_PATH = Path(__file__).resolve().parent.parent / "taxonomy.json"


def load():
    global _DOC
    if _DOC is None:
        _DOC = json.loads(_PATH.read_text(encoding="utf-8"))
        _validate(_DOC)
    return _DOC


def _walk(tree, prefix=""):
    for k, v in tree.items():
        path = "%s/%s" % (prefix, k) if prefix else k
        if "executor" in v:
            yield path, v["executor"]
        else:
            for p in _walk(v, path):
                yield p


def _validate(doc):
    walked = dict(_walk(doc["tree"]))
    assert walked == doc["leaves"], "leaves table != tree walk"
    for cap, path in doc["capability_map"].items():
        assert path in walked, "cap %s at non-leaf %s" % (cap, path)
        assert walked[path] == "tierA", \
            "cap %s at non-tierA leaf %s" % (cap, path)


def leaves():
    return dict(load()["leaves"])


def is_leaf(path):
    return path in load()["leaves"]


def executor(path):
    return load()["leaves"].get(path)


def leaf_of_capability(cap):
    return load()["capability_map"].get(cap)


def depth(path):
    return path.count("/") + 1


def top_domain(path):
    return path.split("/")[0]


# ------------------------------------------------- symbolic placement
def _diff_leaf(task):
    if task.get("at") is not None:
        return "mathematics/calculus/differentiation/evaluate_at_point"
    order = int(task.get("order", 1))
    return {1: "mathematics/calculus/differentiation/first_derivative",
            2: "mathematics/calculus/differentiation/second_derivative",
            }.get(order,
                  "mathematics/calculus/differentiation/higher_order")


OP_LEAF = {
    "differentiate": _diff_leaf,
    "integrate_indef": "mathematics/calculus/integration/indefinite",
    "integrate_def": "mathematics/calculus/integration/definite",
    "limit": lambda t: ("mathematics/calculus/limits/at_infinity"
                        if t.get("point") in ("inf", "oo")
                        else "mathematics/calculus/limits/finite_point"),
    "solve_linear": "mathematics/algebra/linear_solve",
    "solve_poly": "mathematics/algebra/quadratic_polynomial_solve",
    "evaluate": "mathematics/arithmetic/expression_evaluation",
    "sum_finite": "mathematics/sequences_series/finite_sum",
    "seq_term": "mathematics/sequences_series/arithmetic_geometric",
    "gcd": "mathematics/number_theory/gcd_lcm",
    "lcm": "mathematics/number_theory/gcd_lcm",
    "is_prime": "mathematics/number_theory/divisibility_primes",
    "ncr": "mathematics/combinatorics_probability/permutations_combinations",
    "npr": "mathematics/combinatorics_probability/permutations_combinations",
    "probability": "mathematics/combinatorics_probability/basic_probability",
    "logic_eval": "logic/propositional_evaluation",
    "set_op": "logic/set_operations",
    "compare": "logic/comparison_ordering",
}


def place_symbolic(task):
    """Leaf for a structured task, from op + operands only. None when
    no rule applies (the task is then unindexable -> refused)."""
    rule = OP_LEAF.get(task.get("op"))
    if rule is None:
        return None
    path = rule(task) if callable(rule) else rule
    return path if is_leaf(path) else None


if __name__ == "__main__":
    doc = load()
    print("taxonomy ok:", doc["counts"])
    # every OP_LEAF static target is a real leaf
    bad = []
    for op, rule in OP_LEAF.items():
        if not callable(rule) and not is_leaf(rule):
            bad.append((op, rule))
    print("OP_LEAF targets ok" if not bad else "BAD: %s" % bad)
    raise SystemExit(1 if bad else 0)
