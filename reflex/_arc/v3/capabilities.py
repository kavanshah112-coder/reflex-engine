"""Capability registry (Section 17): a minimal reusable computational
vocabulary. Each capability declares typed inputs/output, the governing
equation, an executor expression, preconditions, and a verifier hint.

Capabilities are DOMAIN-REUSABLE by design (Section 3): e.g. heat_to_temp_rise
consumes any energy regardless of which domain produced it. The special
`energy_conservation` capability is an explicit zero-cost transfer marker the
planner inserts when energy crosses domains; path validation treats its
presence/absence as equivalent (Section 21).
"""
import math

# name -> spec
REGISTRY = {
    # ---- mechanics ----
    "potential_energy": {
        "inputs": ["mass", "height"], "output": "energy",
        "equation": "E = m*g*h", "expr": "m0 * 9.8 * h0",
        "domain": "mechanics",
        "pre": lambda s: True,
    },
    "kinetic_energy": {
        "inputs": ["mass", "speed"], "output": "energy",
        "equation": "E = m*v**2/2", "expr": "m0 * v0**2 / 2",
        "domain": "mechanics",
    },
    "work_from_force": {
        "inputs": ["force", "distance"], "output": "energy",
        "equation": "E = F*d", "expr": "f0 * d0",
        "domain": "mechanics",
    },
    "height_from_energy": {
        "inputs": ["energy", "mass"], "output": "height",
        "equation": "h = E/(m*g)", "expr": "e0 / (m0 * 9.8)",
        "domain": "mechanics",
    },
    "speed_from_energy": {
        "inputs": ["energy", "mass"], "output": "speed",
        "equation": "v = sqrt(2*E/m)", "expr": "math.sqrt(2 * e0 / m0)",
        "domain": "mechanics",
        "pre": lambda s: s["e0"] >= 0,
    },
    "force_from_mass_accel": {
        "inputs": ["mass", "accel"], "output": "force",
        "equation": "F = m*a", "expr": "m0 * a0",
        "domain": "mechanics",
    },
    # ---- thermodynamics ----
    "heat_to_temp_rise": {
        "inputs": ["energy", "mass", "spec_heat"], "output": "temp_diff",
        "equation": "dT = E/(m*c)", "expr": "e0 / (m0 * c0)",
        "domain": "thermodynamics",
    },
    "temp_rise_to_heat": {
        "inputs": ["mass", "spec_heat", "temp_diff"], "output": "energy",
        "equation": "E = m*c*dT", "expr": "m0 * c0 * t0",
        "domain": "thermodynamics",
    },
    "carnot_efficiency": {
        "inputs": ["temp_hot", "temp_cold"], "output": "efficiency",
        "equation": "eta = 1 - Tc/Th", "expr": "1 - tc0 / th0",
        "domain": "thermodynamics",
        "pre": lambda s: s["th0"] > s["tc0"] > 0,
    },
    "work_from_heat_eff": {
        "inputs": ["efficiency", "energy"], "output": "energy",
        "equation": "W = eta*Qh", "expr": "eff0 * e0",
        "domain": "thermodynamics",
    },
    # ---- electricity ----
    "electrical_energy": {
        "inputs": ["power", "time"], "output": "energy",
        "equation": "E = P*t", "expr": "p0 * t0",
        "domain": "electricity",
    },
    "power_from_vi": {
        "inputs": ["voltage", "current"], "output": "power",
        "equation": "P = V*I", "expr": "v0 * i0",
        "domain": "electricity",
    },
    "power_from_i2r": {
        "inputs": ["current", "resistance"], "output": "power",
        "equation": "P = I**2*R", "expr": "i0**2 * r0",
        "domain": "electricity",
    },
    "current_from_vr": {
        "inputs": ["voltage", "resistance"], "output": "current",
        "equation": "I = V/R", "expr": "v0 / r0",
        "domain": "electricity",
    },
    "voltage_from_ir": {
        "inputs": ["current", "resistance"], "output": "voltage",
        "equation": "V = I*R", "expr": "i0 * r0",
        "domain": "electricity",
    },
    "charge_from_it": {
        "inputs": ["current", "time"], "output": "charge",
        "equation": "Q = I*t", "expr": "i0 * t0",
        "domain": "electricity",
    },
    # ---- transfer marker (explicit, zero-cost; validator-equivalent) ----
    "energy_conservation": {
        "inputs": ["energy"], "output": "energy",
        "equation": "E_out = E_in", "expr": "e0",
        "domain": "shared", "transfer": True,
    },
}

# slot-variable naming for expr evaluation: first letter(s) of kind + index
_KIND_VAR = {"mass": "m", "height": "h", "distance": "d", "speed": "v",
             "accel": "a", "force": "f", "time": "t", "energy": "e",
             "power": "p", "temp_hot": "th", "temp_cold": "tc",
             "temp_diff": "t", "spec_heat": "c", "current": "i",
             "voltage": "v", "resistance": "r", "charge": "q",
             "efficiency": "eff", "temp": "tt"}


def execute(name, inputs):
    """Deterministic executor: inputs = {kind: Quantity}. Returns (value, ok,
    reason). Analytic-exact FLOPs are negligible and counted as executor ops."""
    spec = REGISTRY[name]
    ns = {"math": math}
    # bind first (and for duplicate-kind formulas, positional) variables
    counts = {}
    for kind in spec["inputs"]:
        q = inputs[kind]
        base = _KIND_VAR[kind]
        idx = counts.get(base, 0)
        counts[base] = idx + 1
        ns[f"{base}{idx}"] = q.value
    pre = spec.get("pre")
    if pre is not None:
        try:
            if not pre(ns):
                return None, False, f"precondition failed for {name}"
        except Exception as e:
            return None, False, f"precondition error: {e}"
    try:
        value = eval(spec["expr"], {"__builtins__": {}, "math": math}, ns)
    except Exception as e:
        return None, False, f"executor error: {e}"
    if not (isinstance(value, (int, float)) and math.isfinite(value)):
        return None, False, "non-finite result"
    return float(value), True, "ok"


def caps_producing(kind):
    return [n for n, s in REGISTRY.items() if s["output"] == kind
            and not s.get("transfer")]


def caps_consuming(kind):
    return [n for n, s in REGISTRY.items() if kind in s["inputs"]
            and not s.get("transfer")]
