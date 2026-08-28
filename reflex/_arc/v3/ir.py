"""Typed intermediate representations (Section 6).

Quantity: a physical quantity with a semantic KIND (not just a unit class),
a canonical unit, and provenance. Capabilities declare input kinds and an
output kind; the planner connects OUTPUT_KIND(A) -> INPUT_KIND(B).
"""
from dataclasses import dataclass, field


# canonical kinds and their canonical units
KINDS = {
    "mass": "kg", "height": "m", "distance": "m", "speed": "m/s",
    "accel": "m/s^2", "force": "N", "time": "s", "energy": "J",
    "power": "W", "temp_hot": "K", "temp_cold": "K", "temp": "K",
    "temp_diff": "K", "spec_heat": "J/(kg*K)", "current": "A",
    "voltage": "V", "resistance": "ohm", "charge": "C",
    "efficiency": "", "pressure": "Pa", "volume": "m^3",
}


# kinds that are CONSUMED when used (extensive, convertible — energy cannot be
# double-counted); every other kind is a reusable parameter (mass, temps, c...)
CONSUMABLE_KINDS = {"energy"}


@dataclass
class Quantity:
    kind: str
    value: float
    unit: str = ""
    source: str = "query"      # query | capability name | conversion
    note: str = ""
    consumed: bool = False

    def __post_init__(self):
        if not self.unit and self.kind in KINDS:
            self.unit = KINDS[self.kind]


@dataclass
class Equation:
    lhs: str
    rhs: str
    source: str = "query"

    def text(self):
        return f"{self.lhs} = {self.rhs}"


@dataclass
class PlanState:
    """Planner state: typed quantities available so far + executed path."""
    quantities: dict = field(default_factory=dict)   # kind -> [Quantity]
    path: list = field(default_factory=list)         # capability names in order
    conversions: list = field(default_factory=list)
    step_sources: list = field(default_factory=list)  # per-step input sources

    def has(self, kind):
        return any(not q.consumed for q in self.quantities.get(kind, []))

    def get(self, kind):
        """First unconsumed quantity of this kind (query-first order)."""
        return next(q for q in self.quantities[kind] if not q.consumed)

    def add(self, q: Quantity):
        self.quantities.setdefault(q.kind, []).append(q)

    def clone(self):
        from dataclasses import replace
        return PlanState(
            {k: [replace(q) for q in v] for k, v in self.quantities.items()},
            list(self.path), list(self.conversions),
            list(self.step_sources))
