"""Canonical action registry — single source of truth.

Concept reflex nodes classify queries into ACTIONS:
  - text actions:    canonical concept answers (with grading rubrics)
  - formula actions: executable numeric schemas (neural net selects, executor computes)
  - function calls:  actions that invoke the derivation function node with a spec id

The derivation function node resolves DERIVATION_SPECS (or parses novel equation sets)
and runs a generic sympy eliminate/solve engine.

Grading rubric format: list of groups; each group is a list of case-insensitive
substrings/regexes; a free-text answer passes if EVERY group is matched by >= 1 entry.
"""

# --------------------------------------------------------------------------------------
# TEXT ACTIONS (canonical concept answers)
# --------------------------------------------------------------------------------------

TEXT_ACTIONS = {
    # ---------------- thermodynamics ----------------
    "thermo.first_law": {
        "domain": "thermodynamics",
        "answer": ("The first law of thermodynamics is the law of energy conservation: "
                   "energy cannot be created or destroyed, only converted between forms. "
                   "For a closed system the change in internal energy equals heat added "
                   "minus work done by the system: ΔU = Q − W."),
        "rubric": [["conserv", "cannot be created", "not be created", "neither created"],
                   ["internal energy", "ΔU", "delta u", "du ="]],
    },
    "thermo.second_law": {
        "domain": "thermodynamics",
        "answer": ("The second law of thermodynamics states that the total entropy of an "
                   "isolated system never decreases; natural processes are irreversible and "
                   "heat flows spontaneously from hot to cold, never the reverse without work."),
        "rubric": [["entropy"],
                   ["increase", "never decrease", "cannot decrease", "hot to cold",
                    "irrevers", "one direction"]],
    },
    "thermo.zeroth_law": {
        "domain": "thermodynamics",
        "answer": ("The zeroth law of thermodynamics: if two systems are each in thermal "
                   "equilibrium with a third system, they are in thermal equilibrium with "
                   "each other. This underpins the definition of temperature."),
        "rubric": [["equilibrium"], ["third", "each other", "temperature"]],
    },
    "thermo.entropy_def": {
        "domain": "thermodynamics",
        "answer": ("Entropy is a state function measuring the disorder or randomness of a "
                   "system — formally, the number of microscopic configurations (microstates) "
                   "consistent with the macroscopic state. It quantifies energy no longer "
                   "available to do useful work; for reversible heat transfer dS = δQ/T."),
        "rubric": [["disorder", "randomness", "microstate", "unavailable", "dispersal",
                    "spread of energy", "q/t"]],
    },
    "thermo.enthalpy_def": {
        "domain": "thermodynamics",
        "answer": ("Enthalpy is a state function defined as H = U + PV (internal energy plus "
                   "pressure–volume product). At constant pressure, the change in enthalpy "
                   "equals the heat absorbed or released by the system."),
        "rubric": [["u + pv", "internal energy plus", "u plus pv", "h = u"],
                   ["constant pressure", "heat"]],
    },
    "thermo.heat_def": {
        "domain": "thermodynamics",
        "answer": ("Heat is energy transferred between systems due to a temperature "
                   "difference, flowing spontaneously from the hotter to the colder body. "
                   "It is a process (path) quantity, not something a body 'contains'."),
        "rubric": [["energy"], ["temperature difference", "hotter", "hot to cold",
                                "temperature gradient"]],
    },
    "thermo.temperature_def": {
        "domain": "thermodynamics",
        "answer": ("Temperature is a measure of the average kinetic energy of the random "
                   "microscopic motion of a system's particles; it determines the direction "
                   "of spontaneous heat flow between bodies."),
        "rubric": [["average kinetic", "mean kinetic", "molecular motion", "particle motion",
                    "thermal equilibrium"]],
    },
    "thermo.specific_heat": {
        "domain": "thermodynamics",
        "answer": ("Specific heat capacity is the amount of heat required to raise the "
                   "temperature of one unit mass (1 kg or 1 g) of a substance by one degree "
                   "(1 K or 1 °C): c = Q/(m·ΔT)."),
        "rubric": [["heat", "energy"], ["unit mass", "1 kg", "one kilogram", "per gram",
                                        "1 g", "per unit mass", "m·ΔT", "m δt", "mΔt"]],
    },
    "thermo.rev_irrev": {
        "domain": "thermodynamics",
        "answer": ("A reversible process is an idealized quasi-static process passing through "
                   "equilibrium states that can be reversed without net entropy production. "
                   "Irreversible (real) processes — with friction, finite temperature "
                   "differences, or rapid changes — generate entropy and cannot be undone "
                   "without leaving changes in the surroundings."),
        "rubric": [["entropy", "equilibrium", "quasi-static", "quasistatic"],
                   ["irrevers", "cannot be", "friction", "real process"]],
    },
    "thermo.heat_work_relation": {
        "domain": "thermodynamics",
        "answer": ("Heat and work are the two ways energy crosses a system boundary. They are "
                   "related through the first law: ΔU = Q − W, so heat added can raise "
                   "internal energy or be converted to work. Work is ordered (organized) "
                   "energy transfer; heat is disordered transfer driven by temperature "
                   "difference, and the second law limits converting heat fully into work."),
        "rubric": [["energy transfer", "transfer of energy", "energy cross",
                    "ways energy", "forms of energy transfer", "first law"],
                   ["ΔU", "delta u", "internal energy", "q - w", "q − w", "q minus w"]],
    },
    "thermo.carnot_principle": {
        "domain": "thermodynamics",
        "answer": ("Carnot's principle: no heat engine operating between two reservoirs can "
                   "be more efficient than a reversible (Carnot) engine between the same "
                   "reservoirs, and that maximum efficiency depends only on the reservoir "
                   "temperatures: η_max = 1 − Tc/Th."),
        "rubric": [["reversible", "carnot"],
                   ["1 - tc/th", "1 − tc/th", "tc/th", "temperature", "most efficient",
                    "maximum efficiency"]],
    },
    "thermo.entropy_efficiency": {
        "domain": "thermodynamics",
        "answer": ("Entropy limits heat-engine efficiency. The engine must reject enough heat "
                   "that total entropy does not decrease: Qc/Tc ≥ Qh/Th. This caps efficiency "
                   "at the Carnot value η ≤ 1 − Tc/Th, and any real (irreversible) entropy "
                   "production lowers efficiency further below that limit."),
        "rubric": [["entropy"],
                   ["reject", "carnot", "1 - tc/th", "1 − tc/th", "waste heat",
                    "cannot decrease", "second law"]],
    },
    "thermo.state_vs_path": {
        "domain": "thermodynamics",
        "answer": ("State functions (internal energy, entropy, enthalpy, temperature, "
                   "pressure) depend only on the current equilibrium state. Path functions "
                   "(heat and work) depend on the specific process taken between states."),
        "rubric": [["state"], ["path", "process", "depend on how", "route"],
                   ["heat", "work"]],
    },
    "thermo.adiabatic_isothermal": {
        "domain": "thermodynamics",
        "answer": ("In an adiabatic process no heat is exchanged (Q = 0), so temperature "
                   "changes as work is done. In an isothermal process temperature is constant "
                   "(ΔT = 0), so for an ideal gas internal energy is constant and any work "
                   "done is balanced by heat flow."),
        "rubric": [["no heat", "q = 0", "q=0", "without heat"],
                   ["constant temperature", "temperature is constant", "same temperature",
                    "isothermal"]],
    },
    "thermo.free_energy": {
        "domain": "thermodynamics",
        "answer": ("Gibbs free energy, G = H − TS, measures the maximum non-expansion work "
                   "obtainable at constant temperature and pressure. A process is spontaneous "
                   "when ΔG < 0."),
        "rubric": [["h - ts", "h − ts", "enthalpy", "g = h"],
                   ["spontaneous", "maximum", "useful work", "available work"]],
    },
    "thermo.efficiency_less_100": {
        "domain": "thermodynamics",
        "answer": ("No heat engine can be 100% efficient because the second law "
                   "(Kelvin–Planck statement) forbids converting heat entirely into work in "
                   "a cycle: some heat must be rejected to a cold reservoir so total entropy "
                   "does not decrease. Efficiency is bounded by the Carnot limit 1 − Tc/Th."),
        "rubric": [["second law", "kelvin", "entropy"],
                   ["reject", "cold reservoir", "waste heat", "carnot", "1 - tc/th",
                    "1 − tc/th"]],
    },
    "thermo.heat_engine_def": {
        "domain": "thermodynamics",
        "answer": ("A heat engine is a device operating in a cycle that absorbs heat from a "
                   "hot reservoir, converts part of it into work, and rejects the remainder "
                   "to a cold reservoir."),
        "rubric": [["cycle", "cyclic"], ["work"], ["heat", "reservoir"]],
    },

    # ---------------- mechanics ----------------
    "mech.newton_first": {
        "domain": "mechanics",
        "answer": ("Newton's first law (law of inertia): a body remains at rest or in uniform "
                   "straight-line motion unless acted on by a net external force."),
        "rubric": [["rest", "uniform", "constant velocity", "straight line", "inertia"],
                   ["force"]],
    },
    "mech.newton_second": {
        "domain": "mechanics",
        "answer": ("Newton's second law: the net force on a body equals its mass times its "
                   "acceleration, F = ma (more generally, force equals the rate of change of "
                   "momentum, F = dp/dt)."),
        "rubric": [["f = ma", "f=ma", "mass times acceleration",
                    "rate of change of momentum", "dp/dt", "ma\\b"]],
    },
    "mech.newton_third": {
        "domain": "mechanics",
        "answer": ("Newton's third law: for every action there is an equal and opposite "
                   "reaction — when body A exerts a force on body B, body B exerts an equal "
                   "and opposite force on body A."),
        "rubric": [["equal"], ["opposite"], ["action", "reaction", "force"]],
    },
    "mech.momentum_def": {
        "domain": "mechanics",
        "answer": ("Momentum is the product of an object's mass and velocity, p = mv. It is a "
                   "vector quantity, and the net external force equals its rate of change."),
        "rubric": [["mass"], ["velocity"], ["p = mv", "p=mv", "product", "times"]],
    },
    "mech.work_energy": {
        "domain": "mechanics",
        "answer": ("The work–energy theorem: the net work done on an object equals its change "
                   "in kinetic energy, W_net = ΔKE = ½mv² − ½mu². Positive net work speeds "
                   "the object up; negative net work slows it down."),
        "rubric": [["work"], ["kinetic energy", "ke", "½mv", "1/2 mv", "mv²", "mv^2"],
                   ["change", "equals", "delta", "Δ"]],
    },
    "mech.cons_momentum": {
        "domain": "mechanics",
        "answer": ("Conservation of momentum: if the net external force on a system is zero, "
                   "its total momentum stays constant. In any collision or explosion the "
                   "total momentum just before equals the total momentum just after."),
        "rubric": [["momentum"], ["constant", "conserved", "same", "unchanged"],
                   ["external force", "no net", "isolated", "collision"]],
    },
    "mech.cons_energy": {
        "domain": "mechanics",
        "answer": ("Conservation of mechanical energy: in the absence of friction and other "
                   "non-conservative forces, the sum of kinetic and potential energy stays "
                   "constant — energy just converts between KE and PE."),
        "rubric": [["kinetic"], ["potential"], ["constant", "conserved", "converts",
                                                "transform"]],
    },
    "mech.friction": {
        "domain": "mechanics",
        "answer": ("Friction is a contact force opposing relative motion (or attempted "
                   "motion) between surfaces. Its magnitude is approximately proportional to "
                   "the normal force, f = μN, and it dissipates mechanical energy as heat."),
        "rubric": [["oppos", "resist"], ["normal force", "μ", "mu", "surfaces", "contact"]],
    },
    "mech.circular": {
        "domain": "mechanics",
        "answer": ("Uniform circular motion requires a centripetal force directed toward the "
                   "center of the circle, producing centripetal acceleration a = v²/r. The "
                   "speed is constant but the velocity direction continuously changes."),
        "rubric": [["center", "centripetal"], ["v²/r", "v^2/r", "v2/r", "toward"]],
    },
    "mech.inertia_def": {
        "domain": "mechanics",
        "answer": ("Inertia is the resistance of an object to changes in its state of motion. "
                   "Mass is the quantitative measure of inertia — more massive objects are "
                   "harder to accelerate."),
        "rubric": [["resist", "opposes change", "tendency"], ["motion"], ["mass"]],
    },
    "mech.mass_weight": {
        "domain": "mechanics",
        "answer": ("Mass is the amount of matter in an object (a scalar, measured in kg) and "
                   "does not change with location. Weight is the gravitational force on that "
                   "mass, w = mg (a vector, in newtons), and varies with local gravity."),
        "rubric": [["matter", "scalar", "amount"], ["force", "mg", "gravit"]],
    },
    "mech.elastic_inelastic": {
        "domain": "mechanics",
        "answer": ("In an elastic collision both momentum and kinetic energy are conserved. "
                   "In an inelastic collision momentum is conserved but kinetic energy is "
                   "not — some converts to heat or deformation; in a perfectly inelastic "
                   "collision the bodies stick together."),
        "rubric": [["momentum"], ["kinetic energy"], ["conserv"],
                   ["not conserved", "lost", "heat", "deformation", "stick"]],
    },
    "mech.projectile": {
        "domain": "mechanics",
        "answer": ("Projectile motion combines constant-velocity horizontal motion with "
                   "uniformly accelerated vertical motion under gravity; the two components "
                   "are independent, producing a parabolic trajectory."),
        "rubric": [["horizontal"], ["vertical"], ["independent", "parabol", "gravity"]],
    },
    "mech.equilibrium": {
        "domain": "mechanics",
        "answer": ("A body is in mechanical equilibrium when the net force and the net torque "
                   "on it are both zero: it is either at rest (static) or moving at constant "
                   "velocity (dynamic equilibrium)."),
        "rubric": [["net force"], ["zero"], ["torque", "rest", "constant velocity"]],
    },
    "mech.impulse_def": {
        "domain": "mechanics",
        "answer": ("Impulse is the product of force and the time over which it acts, J = FΔt, "
                   "and equals the change in momentum it produces: FΔt = Δp."),
        "rubric": [["force"], ["time"], ["momentum", "Δp", "delta p"]],
    },
}

# --------------------------------------------------------------------------------------
# FORMULA ACTIONS (numeric schemas; executor computes from parsed slots)
# `expr` uses slot names; evaluated in a restricted namespace with math functions.
# `steps` > 1 marks multi-step schemas (depth 3).
# --------------------------------------------------------------------------------------

FORMULA_ACTIONS = {
    # ---------------- thermodynamics ----------------
    "thermo.calc.delta_u": {
        "domain": "thermodynamics", "slots": ["Q", "W"], "expr": "Q - W", "unit": "J",
        "steps": 1,
        "template": "By the first law, ΔU = Q − W = {Q} − {W} = {result} J.",
    },
    "thermo.calc.carnot_eff": {
        "domain": "thermodynamics", "slots": ["Tc", "Th"], "expr": "1 - Tc/Th", "unit": "",
        "steps": 1,
        "template": ("Carnot efficiency η = 1 − Tc/Th = 1 − {Tc}/{Th} = {result} "
                     "(≈ {result_pct}%)."),
    },
    "thermo.calc.q_mcdt": {
        "domain": "thermodynamics", "slots": ["m", "c", "dT"], "expr": "m * c * dT",
        "unit": "J", "steps": 1,
        "template": "Q = mcΔT = {m} × {c} × {dT} = {result} J.",
    },
    "thermo.calc.entropy_change": {
        "domain": "thermodynamics", "slots": ["Q", "T"], "expr": "Q / T", "unit": "J/K",
        "steps": 1,
        "template": "For heat transfer at constant temperature, ΔS = Q/T = {Q}/{T} = {result} J/K.",
    },
    "thermo.calc.work_pdv": {
        "domain": "thermodynamics", "slots": ["P", "dV"], "expr": "P * dV", "unit": "J",
        "steps": 1,
        "template": "At constant pressure, W = PΔV = {P} × {dV} = {result} J.",
    },
    "thermo.calc.eff_from_work": {
        "domain": "thermodynamics", "slots": ["Wout", "Qh"], "expr": "Wout / Qh", "unit": "",
        "steps": 1,
        "template": "Efficiency η = W/Q_h = {Wout}/{Qh} = {result} (≈ {result_pct}%).",
    },
    "thermo.calc.carnot_work": {
        "domain": "thermodynamics", "slots": ["Tc", "Th", "Qh"],
        "expr": "(1 - Tc/Th) * Qh", "unit": "J", "steps": 2,
        "template": ("First, η = 1 − Tc/Th = 1 − {Tc}/{Th}. "
                     "Then maximum work W = ηQ_h = {result} J."),
    },
    "thermo.calc.qc_reject": {
        "domain": "thermodynamics", "slots": ["Qh", "Wout"], "expr": "Qh - Wout", "unit": "J",
        "steps": 1,
        "template": "Energy balance over a cycle: Q_c = Q_h − W = {Qh} − {Wout} = {result} J.",
    },

    # ---------------- mechanics ----------------
    "mech.calc.f_ma": {
        "domain": "mechanics", "slots": ["m", "a"], "expr": "m * a", "unit": "N", "steps": 1,
        "template": "F = ma = {m} × {a} = {result} N.",
    },
    "mech.calc.a_from_f": {
        "domain": "mechanics", "slots": ["F", "m"], "expr": "F / m", "unit": "m/s^2",
        "steps": 1,
        "template": "a = F/m = {F}/{m} = {result} m/s².",
    },
    "mech.calc.momentum": {
        "domain": "mechanics", "slots": ["m", "v"], "expr": "m * v", "unit": "kg*m/s",
        "steps": 1,
        "template": "p = mv = {m} × {v} = {result} kg·m/s.",
    },
    "mech.calc.ke": {
        "domain": "mechanics", "slots": ["m", "v"], "expr": "0.5 * m * v**2", "unit": "J",
        "steps": 1,
        "template": "KE = ½mv² = 0.5 × {m} × {v}² = {result} J.",
    },
    "mech.calc.work": {
        "domain": "mechanics", "slots": ["F", "d"], "expr": "F * d", "unit": "J", "steps": 1,
        "template": "W = Fd = {F} × {d} = {result} J.",
    },
    "mech.calc.pe": {
        "domain": "mechanics", "slots": ["m", "h"], "expr": "m * 9.8 * h", "unit": "J",
        "steps": 1,
        "template": "PE = mgh = {m} × 9.8 × {h} = {result} J.",
    },
    "mech.calc.v_uat": {
        "domain": "mechanics", "slots": ["u", "a", "t"], "expr": "u + a * t", "unit": "m/s",
        "steps": 1,
        "template": "v = u + at = {u} + {a} × {t} = {result} m/s.",
    },
    "mech.calc.s_ut": {
        "domain": "mechanics", "slots": ["u", "a", "t"], "expr": "u * t + 0.5 * a * t**2",
        "unit": "m", "steps": 1,
        "template": "s = ut + ½at² = {u} × {t} + 0.5 × {a} × {t}² = {result} m.",
    },
    "mech.calc.centripetal": {
        "domain": "mechanics", "slots": ["m", "v", "r"], "expr": "m * v**2 / r", "unit": "N",
        "steps": 1,
        "template": "F_c = mv²/r = {m} × {v}²/{r} = {result} N.",
    },
    "mech.calc.impulse": {
        "domain": "mechanics", "slots": ["F", "t"], "expr": "F * t", "unit": "N*s", "steps": 1,
        "template": "Impulse J = FΔt = {F} × {t} = {result} N·s (= momentum change).",
    },
    "mech.calc.inelastic_v": {
        "domain": "mechanics", "slots": ["m1", "v1", "m2", "v2"],
        "expr": "(m1*v1 + m2*v2) / (m1 + m2)", "unit": "m/s", "steps": 2,
        "template": ("Momentum conservation: v = (m₁v₁ + m₂v₂)/(m₁ + m₂) = "
                     "({m1}×{v1} + {m2}×{v2})/({m1} + {m2}) = {result} m/s."),
    },
    "mech.calc.v_from_fd": {
        "domain": "mechanics", "slots": ["F", "m", "d"], "expr": "sqrt(2 * F * d / m)",
        "unit": "m/s", "steps": 2,
        "template": ("Work–energy: Fd = ½mv², so v = √(2Fd/m) = √(2×{F}×{d}/{m}) "
                     "= {result} m/s."),
    },
}

# --------------------------------------------------------------------------------------
# DERIVATION SPECS (resolved by the derivation function node; executed with sympy)
# given:      list of sympy Eq strings
# eliminate:  symbols to eliminate
# solve_for:  the symbol whose relation we want (lhs of target)
# target:     canonical result relation (for verification)
# domains:    which concept domains use this derivation
# --------------------------------------------------------------------------------------

DERIVATION_SPECS = {
    "deriv.kinematics.v2": {
        "symbols": "v u a t s",
        "given": ["Eq(v, u + a*t)", "Eq(s, u*t + a*t**2/2)"],
        "eliminate": ["t"],
        "solve_for": "v",
        "target": "Eq(v**2, u**2 + 2*a*s)",
        "domains": ["mechanics", "derivation"],
        "nl": "Derive v² = u² + 2as from v = u + at and s = ut + ½at².",
    },
    "deriv.kinematics.s": {
        "symbols": "v u a t s",
        "given": ["Eq(v, u + a*t)", "Eq(s, (u + v)*t/2)"],
        "eliminate": ["v"],
        "solve_for": "s",
        "target": "Eq(s, u*t + a*t**2/2)",
        "domains": ["mechanics", "derivation"],
        "nl": "Derive s = ut + ½at² from v = u + at and s = (u+v)t/2.",
    },
    "deriv.work_energy": {
        "symbols": "Wk F m a v u s",
        "given": ["Eq(Wk, F*s)", "Eq(F, m*a)", "Eq(v**2, u**2 + 2*a*s)"],
        "eliminate": ["F", "a"],
        "solve_for": "Wk",
        "target": "Eq(Wk, m*v**2/2 - m*u**2/2)",
        "domains": ["mechanics", "derivation"],
        "nl": "Derive the work–energy theorem W = ½mv² − ½mu² from W = Fs, F = ma and v² = u² + 2as.",
    },
    "deriv.ke_momentum": {
        "symbols": "KE p m v",
        "given": ["Eq(p, m*v)", "Eq(KE, m*v**2/2)"],
        "eliminate": ["v"],
        "solve_for": "KE",
        "target": "Eq(KE, p**2/(2*m))",
        "domains": ["mechanics", "derivation"],
        "nl": "Derive KE = p²/(2m) from p = mv and KE = ½mv².",
    },
    "deriv.efficiency_relation": {
        "symbols": "eta Wo Qh Qc",
        "given": ["Eq(eta, Wo/Qh)", "Eq(Wo, Qh - Qc)"],
        "eliminate": ["Wo"],
        "solve_for": "eta",
        "target": "Eq(eta, 1 - Qc/Qh)",
        "domains": ["thermodynamics", "derivation"],
        "nl": "Derive η = 1 − Qc/Qh from η = W/Qh and W = Qh − Qc.",
    },
    "deriv.carnot_eff": {
        "symbols": "eta Wo Qh Qc Tc Th",
        "given": ["Eq(eta, Wo/Qh)", "Eq(Wo, Qh - Qc)", "Eq(Qc/Qh, Tc/Th)"],
        "eliminate": ["Wo", "Qc"],
        "solve_for": "eta",
        "target": "Eq(eta, 1 - Tc/Th)",
        "domains": ["thermodynamics", "derivation"],
        "nl": ("Derive the Carnot efficiency η = 1 − Tc/Th from η = W/Qh, W = Qh − Qc, "
               "and Qc/Qh = Tc/Th."),
    },
    "deriv.first_law_q": {
        "symbols": "dU Q Wo",
        "given": ["Eq(dU, Q - Wo)"],
        "eliminate": [],
        "solve_for": "Q",
        "target": "Eq(Q, dU + Wo)",
        "domains": ["thermodynamics", "derivation"],
        "nl": "Rearrange the first law ΔU = Q − W to express Q.",
    },
    "deriv.freefall_v": {
        "symbols": "v g h m",
        "given": ["Eq(m*g*h, m*v**2/2)"],
        "eliminate": [],
        "solve_for": "v",
        "target": "Eq(v, sqrt(2*g*h))",
        "domains": ["mechanics", "thermodynamics", "derivation"],
        "nl": ("Using energy conservation (mgh = ½mv²), derive the speed of an object "
               "after falling from height h."),
        "positive_root": True,
    },
    "deriv.carnot_work": {
        "symbols": "Wo Qh eta Tc Th",
        "given": ["Eq(eta, 1 - Tc/Th)", "Eq(Wo, eta*Qh)"],
        "eliminate": ["eta"],
        "solve_for": "Wo",
        "target": "Eq(Wo, Qh*(1 - Tc/Th))",
        "domains": ["thermodynamics", "derivation"],
        "nl": ("Derive the maximum work W = Qh(1 − Tc/Th) obtainable from heat Qh with "
               "reservoirs at Th and Tc."),
    },
    "deriv.pressure_force": {
        "symbols": "P F A m a",
        "given": ["Eq(P, F/A)", "Eq(F, m*a)"],
        "eliminate": ["F"],
        "solve_for": "P",
        "target": "Eq(P, m*a/A)",
        "domains": ["mechanics", "derivation"],
        "nl": "Derive P = ma/A from P = F/A and F = ma.",
    },
}

# Actions that invoke the derivation node from a concept node ("call.<spec_id>")
FUNCTION_CALL_ACTIONS = {
    f"call.{spec_id}": {"domain": spec["domains"][0], "spec": spec_id}
    for spec_id, spec in DERIVATION_SPECS.items()
}


def node_action_vocab(domain):
    """Ordered action vocabulary for a concept node (text + formula + function calls)."""
    vocab = [k for k, v in TEXT_ACTIONS.items() if v["domain"] == domain]
    vocab += [k for k, v in FORMULA_ACTIONS.items() if v["domain"] == domain]
    vocab += [f"call.{sid}" for sid, s in DERIVATION_SPECS.items() if domain in s["domains"]]
    return sorted(vocab)


def derivation_vocab():
    """Ordered class list for the derivation node: known specs + PARSE + UNKNOWN."""
    return sorted(DERIVATION_SPECS.keys()) + ["PARSE_GENERIC", "UNKNOWN"]
