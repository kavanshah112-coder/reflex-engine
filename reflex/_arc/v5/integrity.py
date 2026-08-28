"""V0.5 state-integrity gate (Section 20).

Sits between PARSER and PLANNER. V0.4 showed the error predictor collapses
to ~random AUROC under parser corruption (0.51 @ 20% noise), so corruption
must be caught STRUCTURALLY before computation, not predicted after.

Checks (all registry/domain-level, none tuned on any evaluation split):
  C1 schema        every quantity has a registry-known kind + finite value
  C2 domain_range  per-kind plausibility ranges (physical/financial sanity)
  C3 duplicates    two quantities of the same kind with conflicting values
  C4 count_parse   numeric literals present in the text vs quantities
                   parsed — a shortfall means a number was dropped/ignored
                   (catches the 'drop' corruption mode directly)
  C5 kind_support  a parsed kind that no capability consumes AND that is
                   not the asked kind is suspicious (catches kind-flips
                   into consumer-less kinds)

Verdict: list of flags; the engine treats any HARD flag as "state
unsafe" -> refuse reflex computation and escalate the whole query to the
LLM (or abstain in pure mode). SOFT flags are recorded but do not block.

False positives cost energy (needless escalation); false negatives cost
correctness. Both rates are measured in the noise experiment.
"""
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v4.registry_v4 import REGISTRY  # noqa: E402

# per-kind plausibility ranges (value AFTER qparse4 unit conversion).
# Deliberately WIDE: these encode impossibility, not typicality.
RANGES = {
    "rate": (0.0, 1.0), "rate_tax": (0.0, 1.0), "rate_discount": (0.0, 1.0),
    "rate_interest": (0.0, 1.0), "years": (0.0, 500.0),
    "count": (0.0, 1e9), "count_breakeven": (0.0, 1e9),
    "mass": (0.0, 1e12), "area": (0.0, 1e9), "volume": (0.0, 1e9),
    "length": (0.0, 1e7), "width": (0.0, 1e7), "thickness": (0.0, 1e5),
    "density": (0.1, 30000.0), "coverage_per_liter": (0.05, 1000.0),
    "voltage": (0.0, 1e6), "current": (0.0, 1e5), "time_s": (0.0, 1e9),
    "power": (0.0, 1e9), "energy_j": (0.0, 1e15),
}
_NEVER_NEGATIVE_PREFIXES = ("price", "cost", "unit_cost", "fixed_cost",
                            "principal", "revenue", "money", "mass",
                            "area", "volume", "density")

_NUM_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w%])")


def _consumed_kinds(registry):
    ks = set()
    for spec in registry.values():
        ks.update(spec["inputs"])
    return ks


def check_state(query, quantities, asked, registry=None):
    """Return {"flags": [...], "hard": bool}. Each flag:
    {"check": C*, "detail": str, "hard": bool}."""
    reg = registry if registry is not None else REGISTRY
    flags = []

    def add(check, detail, hard):
        flags.append({"check": check, "detail": detail, "hard": hard})

    consumed = _consumed_kinds(reg)
    for q in quantities:
        if q.value is None or not math.isfinite(q.value):
            add("C1_schema", f"{q.kind}: non-finite value", True)
            continue
        lo, hi = RANGES.get(q.kind, (None, None))
        if lo is not None and not (lo <= q.value <= hi):
            add("C2_domain_range",
                f"{q.kind}={q.value:g} outside [{lo:g},{hi:g}]", True)
        if q.value < 0 and any(q.kind.startswith(p)
                               for p in _NEVER_NEGATIVE_PREFIXES):
            add("C2_domain_range", f"{q.kind}={q.value:g} negative", True)
        if q.kind not in consumed and q.kind != asked and \
                not any(q.kind.startswith(p) for p in ("money",)):
            add("C5_kind_support",
                f"{q.kind}: no capability consumes it", False)
    # C3 duplicates/conflicts
    by_kind = {}
    for q in quantities:
        by_kind.setdefault(q.kind, []).append(q.value)
    for kind, vals in by_kind.items():
        if len(vals) > 1:
            lo, hi = min(vals), max(vals)
            if lo <= 0 or hi / max(lo, 1e-12) > 1.0001:
                add("C3_duplicate",
                    f"{kind}: conflicting values {vals}", True)
    # C4 literal-count vs parsed-count
    n_literals = len(_NUM_RE.findall(query))
    if n_literals > 0 and len(quantities) < n_literals:
        # some templates legitimately contain a number the parser folds
        # into a unit (rare); a shortfall of >=1 is still the strongest
        # available drop signal — HARD only when >=2 short or none parsed
        short = n_literals - len(quantities)
        add("C4_count_parse",
            f"{n_literals} numeric literals but {len(quantities)} parsed "
            f"quantities", short >= 2 or len(quantities) == 0)
    return {"flags": flags,
            "hard": any(f["hard"] for f in flags),
            "n_literals": n_literals, "n_parsed": len(quantities)}
