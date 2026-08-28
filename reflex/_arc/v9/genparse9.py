# -*- coding: utf-8 -*-
"""V0.9 parser benchmark (spec Section 7 categories A-Z), adversarial
SQR suite (Sections 4/21), and the new frozen external set EXT9
(Section 30).

Ground truth per parse item:
  {"quantities": [{"concept", "value", "unit"(opt), "role",
                   "concept_alt"(opt list)}],
   "target": kind, "n_entities": int, "category": "A".."Z"}
Roles follow the SQR schema; the grader consumes this directly.
"""
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RAW = ROOT / "results" / "raw_v9"

W = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
     8: "eight", 9: "nine", 12: "twelve", 20: "twenty", 25: "twenty-five",
     40: "forty", 50: "fifty"}

DEV_N = ["crate", "trolley", "flywheel", "pump", "boiler"]
SEAL_N = ["gondola", "capstan", "autoclave", "centrifuge", "monorail car"]
DEV_X = ["handcart", "toboggan"]
SEAL_X = ["palanquin", "bathysphere", "trebuchet"]
DEV_VB = ["moves", "travels"]
SEAL_VB = ["trundles", "careens", "sashays"]


def q(c, v, role="input", unit=None, alt=None):
    d = {"concept": c, "value": float(v), "role": role}
    if unit:
        d["unit"] = unit
    if alt:
        d["concept_alt"] = alt
    return d


def CATS(rng, V, XN, VB):
    """Return list of (category, text, truth) using vocab pools."""
    n1 = rng.choice(V)
    n2 = rng.choice([x for x in V if x != n1])
    xn = rng.choice(XN)
    vb = rng.choice(VB)
    m = rng.choice([2, 3, 5, 8])
    v = rng.choice([4, 6, 9, 12])
    h = rng.choice([7, 20, 40])
    p = rng.choice([15, 40, 90])
    r = rng.choice([5, 7, 12])
    out = []

    out.append(("A", f"The {n1} has a mass of {m} kg. It {vb} at "
                f"{v} m/s. What is its kinetic energy?",
                {"quantities": [q("mass", m, unit="kg"),
                                q("speed", v, unit="m/s")],
                 "target": "energy", "n_entities": 1}))
    out.append(("B", f"The {n1}'s heft comes to {m} kg and its pace is "
                f"{v} m/s. Find the energy of motion.",
                {"quantities": [q("mass", m, unit="kg"),
                                q("speed", v, unit="m/s")],
                 "target": "energy", "n_entities": 1}))
    out.append(("C", f"At {v} m/s — carrying {m} kg — the {n1} keeps "
                "going. How much kinetic energy is that?",
                {"quantities": [q("mass", m, unit="kg"),
                                q("speed", v, unit="m/s")],
                 "target": "energy", "n_entities": 1}))
    out.append(("D", f"The {n1} weighs {W[m]} kilograms and is lifted "
                f"{W[h]} metres. How much potential energy is stored?",
                {"quantities": [q("mass", m, unit="kilograms"),
                                q("height", h, unit="metres")],
                 "target": "energy", "n_entities": 1}))
    out.append(("E", f"Half a litre of solution holds {m} mol of "
                "solute. What is the concentration?",
                {"quantities": [q("solution_volume", 0.5, unit="L"),
                                q("moles", m, unit="mol")],
                 "target": "concentration", "n_entities": 1}))
    out.append(("F", f"Profits are taxed at {r}%. The {n1} business "
                f"cleared ${p * 100} of profit. What remains after tax?",
                {"quantities": [q("rate_tax", r, unit="%"),
                                q("profit", p * 100, unit="$")],
                 "target": "net_profit", "n_entities": 1}))
    out.append(("G", f"A capacitor bank releases {v}.5e3 J into a "
                f"{m} kg block with specific heat 900 J/kg/K. "
                "What temperature rise results?",
                {"quantities": [q("energy", float(f"{v}.5e3"), unit="J"),
                                q("mass", m, unit="kg"),
                                q("spec_heat", 900, unit="J/kg/K")],
                 "target": "temp_diff", "n_entities": 1}))
    out.append(("H", f"The {n1} is milled from stock of density "
                f"{m * 1000} kg/m^3 and measures {v / 10} m^3. "
                "What is its mass?",
                {"quantities": [q("density", m * 1000, unit="kg/m^3"),
                                q("volume", v / 10, unit="m^3")],
                 "target": "mass", "n_entities": 1}))
    out.append(("I", f"The {n1} covers ground at {v * 18} km/h. Its "
                f"mass is {m} tonnes. Compute the kinetic energy.",
                {"quantities": [q("speed", v * 18, unit="km/h"),
                                q("mass", m * 1000, unit="tonnes")],
                 "target": "energy", "n_entities": 1}))
    out.append(("J", f"The {n1} carries {m} kg while the {n2} carries "
                f"{m + 3} kg. The {n1} is hoisted {h} m. How much "
                f"potential energy does the {n1} gain?",
                {"quantities": [q("mass", m, unit="kg"),
                                q("mass", m + 3, role="distractor",
                                  unit="kg"),
                                q("height", h, unit="m")],
                 "target": "energy", "n_entities": 2}))
    out.append(("K", f"A run of {p} units sells at ${v + 20} each, "
                f"costs ${v} each to make, with ${p * 10} fixed. "
                "What is the profit?",
                {"quantities": [q("count", p, unit="units"),
                                q("price_per_unit", v + 20, unit="$"),
                                q("unit_cost", v, unit="$"),
                                q("fixed_cost", p * 10, unit="$")],
                 "target": "profit", "n_entities": 1}))
    out.append(("L", f"The {n1} of {m} kg {vb} at {v} m/s. The workshop "
                f"clock reads {h} past the hour. What is the kinetic "
                "energy?",
                {"quantities": [q("mass", m, unit="kg"),
                                q("speed", v, unit="m/s"),
                                q("time", h, role="distractor")],
                 "target": "energy", "n_entities": 1}))
    out.append(("M", f"Either the {n1} or the {n2} — records disagree "
                f"— has a mass of {m} kg; the other is unweighed. The "
                f"{n1} {vb} at {v} m/s. What is the {n1}'s kinetic "
                "energy?",
                {"quantities": [q("mass", m, unit="kg",
                                  role="input"),
                                q("speed", v, unit="m/s")],
                 "target": "energy", "n_entities": 2,
                 "expect_ambiguous": True}))
    out.append(("N", f"A dozen {n1}s are produced each day at a cost "
                f"of ${v} apiece. What is the daily variable cost?",
                {"quantities": [q("count", 12, unit="units"),
                                q("unit_cost", v, unit="$")],
                 "target": "cost_var", "n_entities": 1}))
    out.append(("O", f"The {n2} holds twice the {m} kg that the {n1} "
                f"holds. The {n1} is winched {h} m up. What potential "
                f"energy does the {n1} gain?",
                {"quantities": [q("mass", m, unit="kg"),
                                q("height", h, unit="m")],
                 "target": "energy", "n_entities": 2}))
    out.append(("P", f"The {n1} is not {m + 4} kg as the manifest "
                f"claims, but {W[m]} kilograms. Hoisted {h} m, what "
                "potential energy does it store?",
                {"quantities": [q("mass", m + 4, role="negated",
                                  unit="kg"),
                                q("mass", m, unit="kilograms"),
                                q("height", h, unit="m")],
                 "target": "energy", "n_entities": 1}))
    out.append(("Q", f"Last season the {n1} sold for ${p} per unit; "
                f"today it sells for ${p + 10} per unit. {v * 10} units "
                "move today. What is today's revenue?",
                {"quantities": [q("price_per_unit", p, role="historical",
                                  unit="$"),
                                q("price_per_unit", p + 10, unit="$"),
                                q("count", v * 10, unit="units")],
                 "target": "revenue", "n_entities": 1}))
    out.append(("R", f"If the {n1} were {m + 6} kg the winch would "
                f"stall; in fact it is {m} kg and rises {h} m. What "
                "potential energy does it gain?",
                {"quantities": [q("mass", m + 6, role="hypothetical",
                                  unit="kg"),
                                q("mass", m, unit="kg"),
                                q("height", h, unit="m")],
                 "target": "energy", "n_entities": 1}))
    out.append(("S", f"The {n1}, which the {n2} that hauls {m + 3} kg "
                f"follows, itself carries {m} kg at {v} m/s. What is "
                f"the {n1}'s kinetic energy?",
                {"quantities": [q("mass", m + 3, role="distractor",
                                  unit="kg"),
                                q("mass", m, unit="kg"),
                                q("speed", v, unit="m/s")],
                 "target": "energy", "n_entities": 2}))
    out.append(("T", f"What is the kinetic energy, given that {m} kg "
                f"is the {n1}'s mass and {v} m/s its speed?",
                {"quantities": [q("mass", m, unit="kg"),
                                q("speed", v, unit="m/s")],
                 "target": "energy", "n_entities": 1}))
    out.append(("U", f"The {xn} registers {m} kg on the scale and "
                f"{vb} at {v} m/s. Kinetic energy?",
                {"quantities": [q("mass", m, unit="kg"),
                                q("speed", v, unit="m/s")],
                 "target": "energy", "n_entities": 1}))
    out.append(("V", f"The {n1} {rng.choice(SEAL_VB)} along at {v} m/s "
                f"bearing {m} kg. How much kinetic energy?",
                {"quantities": [q("mass", m, unit="kg"),
                                q("speed", v, unit="m/s")],
                 "target": "energy", "n_entities": 1}))
    out.append(("W", f"The cryostat's enthalpy throughput is {p} W "
                f"sustained for {h * 60} seconds. How much energy "
                "flows?",
                {"quantities": [q("power", p, unit="W",
                                  alt=["UNKNOWN"]),
                                q("time", h * 60, unit="s")],
                 "target": "energy", "n_entities": 1}))
    out.append(("X", f"{m} kg of coolant absorbs {p * 100} J (specific "
                f"heat 4186 J/kg/K). How much warmer does it get?",
                {"quantities": [q("mass", m, unit="kg"),
                                q("energy", p * 100, unit="J"),
                                q("spec_heat", 4186, unit="J/kg/K")],
                 "target": "temp_diff", "n_entities": 1}))
    out.append(("Y", f"The {n1} drops {h} m carrying {m} kg, and every "
                "joule of the fall heats 2 kg of oil (2000 J/kg/K). "
                "What temperature rise results?",
                {"quantities": [q("height", h, unit="m"),
                                q("mass", m, unit="kg"),
                                q("mass", 2, unit="kg"),
                                q("spec_heat", 2000, unit="J/kg/K")],
                 "target": "temp_diff", "n_entities": 2}))
    out.append(("Z", f"A {p}-unit batch sells at ${v + 20} each; the "
                f"{n1} that stamps them draws {m * 100} W for "
                f"{h * 60} seconds. What is the revenue?",
                {"quantities": [q("count", p, unit="units"),
                                q("price_per_unit", v + 20, unit="$"),
                                q("power", m * 100, role="distractor",
                                  unit="W"),
                                q("time", h * 60, role="distractor",
                                  unit="s")],
                 "target": "revenue", "n_entities": 2}))
    return out


def make_parse(seed, V, XN, VB, reps, tag):
    rng = random.Random(seed)
    items = []
    for rep in range(reps):
        for cat, text, truth in CATS(rng, V, XN, VB):
            truth = {**truth, "category": cat}
            items.append({"id": f"pb{tag}{len(items):04d}", "q": text,
                          "truth": truth, "category": cat})
    return items


# ------------------------------------------------- adversarial suite
def make_adv(seed, V, reps=8):
    rng = random.Random(seed)
    items = []
    mk = 0

    def add(cls, text, trap_value, truth_inputs, target,
            expect=None):
        nonlocal mk
        items.append({"id": f"adv{mk:04d}", "q": text, "class": cls,
                      "trap_value": trap_value,
                      "truth": {"quantities": truth_inputs,
                                "target": target, "n_entities": 1,
                                "category": "ADV"},
                      "expect": expect or "trap_not_input"})
        mk += 1

    for i in range(reps):
        n1 = rng.choice(V)
        n2 = rng.choice([x for x in V if x != n1])
        m = rng.choice([3, 5, 8])
        v = rng.choice([4, 9, 12])
        t = rng.choice([25, 60, 84])
        add("irrelevant", f"Gate {t} stands open. The {n1} of {m} kg "
            f"moves at {v} m/s. Kinetic energy?", t,
            [q("mass", m), q("speed", v)], "energy")
        add("misleading_near", f"The {n1} ({m} kg) passes marker "
            f"{t} while moving at {v} m/s. Kinetic energy?", t,
            [q("mass", m), q("speed", v)], "energy")
        add("contradictory", f"The log lists the {n1} at {m} kg and "
            f"also at {m + t} kg. It moves at {v} m/s. Kinetic "
            "energy?", None,
            [q("speed", v)], "energy", expect="flag_or_abstain")
        add("similar_entities", f"The {n1} A weighs {m} kg; the {n1} "
            f"B weighs {t} kg. {n1} A moves at {v} m/s. What is "
            f"{n1} A's kinetic energy?", t,
            [q("mass", m), q("speed", v)], "energy")
        add("wrong_unit_attach", f"The {n1} of {m} kg covers "
            f"{t} seconds of track at {v} m/s. Kinetic energy?", t,
            [q("mass", m), q("speed", v)], "energy")
        add("wrong_entity_bind", f"The {n2} weighs {t} kg. The {n1}, "
            f"at {m} kg, moves at {v} m/s. The {n1}'s kinetic "
            "energy?", t,
            [q("mass", m), q("speed", v)], "energy")
        add("implied_nonexistent", f"The {n1} moves at {v} m/s with "
            "its usual load. Kinetic energy?", None,
            [q("speed", v)], "energy", expect="flag_or_abstain")
        add("negated", f"No longer {t} kg after unloading, the {n1} "
            f"is now {m} kg, moving at {v} m/s. Kinetic energy?", t,
            [q("mass", m), q("speed", v)], "energy")
        add("hypothetical", f"Were it loaded to {t} kg the {n1} would "
            f"crawl; it actually masses {m} kg at {v} m/s. Kinetic "
            "energy?", t,
            [q("mass", m), q("speed", v)], "energy")
        add("quoted", f"The sign reads '{t} kg limit'. The {n1} "
            f"masses {m} kg and moves at {v} m/s. Kinetic energy?", t,
            [q("mass", m), q("speed", v)], "energy")
        add("example", f"For instance, a {t} kg case would need care. "
            f"Our {n1} is {m} kg at {v} m/s. Its kinetic energy?", t,
            [q("mass", m), q("speed", v)], "energy")
        add("if_clause", f"If the belt ran at {t} m/s it would jam. "
            f"It runs at {v} m/s carrying {m} kg. Kinetic energy?", t,
            [q("mass", m), q("speed", v)], "energy")
        add("historical", f"The {n1} once massed {t} kg; refitted, it "
            f"is {m} kg and does {v} m/s. Kinetic energy?", t,
            [q("mass", m), q("speed", v)], "energy")
    return items


# ------------------------------------------------------------- EXT9
def make_ext9():
    """Hand-authored external set: new registers (log entries, memos,
    dialogue), new nouns, unseen phrasings. answer=None => correct
    behavior is abstain/escalate-without-numeric."""
    E = []

    def add(text, answer, kind, note=""):
        E.append({"id": f"e9.{len(E):02d}", "q": text, "answer": answer,
                  "kind": kind, "note": note})

    add("Maintenance log, 06:14 — hoisted the ballast pod (mass "
        "reading: nineteen kilograms) up the service shaft, 22 m "
        "vertical. Log the stored potential energy in joules.",
        19 * 9.8 * 22, "energy")
    add("Customer email: 'You quoted $18 apiece on the 240 lanterns "
        "and $6.50 to fabricate each. Warehouse rent is a flat $940.' "
        "— what profit does the order book show?",
        240 * 18 - (240 * 6.5 + 940), "profit")
    add("Bench notes: dissolved 29.25 g of the salt (M = 58.5 g/mol) "
        "and topped up to 2.5 litres. State the molarity.",
        (29.25 / 58.5) / 2.5, "concentration")
    add("QA thread — Q: our 16 boiler readings total 384, and the "
        "squared deviations add to 144. One boiler read 27. A: "
        "compute its standard score.",
        (27 - 384 / 16) / ((144 / 16) ** 0.5), "z_score")
    add("Pitch memo: the walking-tour outfit burns $5,400 of ads a "
        "quarter for 90 sign-ups; members churn at 6% monthly and "
        "each yields $14 of monthly margin. Give LTV over CAC.",
        (14 / 0.06) / (5400 / 90), "ltv_cac")
    add("Telegraphic: dray 1,100 kg — 21.6 km/h — full stop — heat "
        "sink 30 kg bronze, c = 380. Degrees of warming?",
        (0.5 * 1100 * 6 ** 2) / (30 * 380), "temp_diff")
    add("The mill wheel's paddle sweep is 3.5 m by 0.8 m; the oak "
        "blank is 0.06 m thick with density 690 kg/m^3. Its mass, "
        "please.", 3.5 * 0.8 * 0.06 * 690, "mass")
    add("Ferry schedule footnote: the auxiliary coil (14 ohms) on the "
        "110 V circuit warms the cabin for 25 minutes. Energy drawn, "
        "in joules?", (110 * 110 / 14) * 25 * 60, "energy")
    add("Ledger: principal parked, £-equivalent $7,500, simple "
        "interest 4 percent, held six years. Interest accrued?",
        7500 * 0.04 * 6, "interest")
    add("Rig check: the winch motor pulls 9 A off 48 V. What power "
        "does it draw?", 9 * 48, "power")
    add("Two crucibles: the larger holds 5 kg of flux, the smaller "
        "2 kg. Only the smaller is heated, absorbing 25,116 J "
        "(c = 4186). How much warmer does the smaller get?",
        25116 / (2 * 4186), "temp_diff")
    add("Stall chatter: 'Mugs? Threw four hundred at the kiln, "
        "twelve dollars each at the till, four-fifty in clay per "
        "piece, and the pitch fee's three hundred flat.' What do "
        "they clear?", 400 * 12 - (400 * 4.5 + 300), "profit")
    add("Sample prep: stock at 1.8 mol/L cut by a factor of 12. "
        "Final concentration?", 1.8 / 12, "final_concentration")
    add("Derrick diary: counterweight up 31 m, mass six hundred "
        "kilograms. Stored energy?", 600 * 9.8 * 31, "energy")
    add("The signal hut's storage heater is rated 2.4 kW and runs "
        "for 40 minutes. How many joules is that?",
        2400 * 40 * 60, "energy")
    add("Refit note: hull plate 2.2 m x 1.4 m x 0.03 m, wrought "
        "bronze at 8,700 kg per cubic metre, bought at $2.10 the "
        "kilogram. Material outlay?",
        2.2 * 1.4 * 0.03 * 8700 * 2.10, "cost_var")
    add("Survey desk: 25 tide gauges sum to 625; squared deviations "
        "total 400. Variance of the series?", 400 / 25, "variance")
    add("The funicular counter reports 84 fare-payers at $3.25 a "
        "ride. Take for the day?", 84 * 3.25, "revenue")
    add("Kiln ticket: reaction ran at 82% yield from 0.75 mol of "
        "feedstock. Product moles?", 0.75 * 0.82, "product_moles")
    add("Dockside: the gantry lowers a 450 kg spool from 12 m; all "
        "of the fall's energy lands in a 60 kg damper block, "
        "c = 500. Temperature climb?",
        450 * 9.8 * 12 / (60 * 500), "temp_diff")
    add("Night audit: ad spend $12,000 brought 300 sign-ups. "
        "Acquisition cost each?", 40.0, "cac")
    add("Brief: the sluice pump does 7,200 J of work every cycle "
        "against 480 N of drag. Over what distance does it push?",
        None, None, "inverse ask (distance from work/force) — no "
        "registry path; correct behavior: escalate or abstain, and "
        "an LLM-step answer of 15 m is acceptable if typed")
    add("Weigh-in: the barge tips the scale at 3.2 tonnes and makes "
        "9 km/h upstream. Kinetic energy?",
        0.5 * 3200 * 2.5 ** 2, "energy")
    add("Chem shelf: 0.4 mol dissolved into 1.6 L. Molarity?",
        0.25, "concentration")
    add("The atelier's tax accountant: gross profit $23,000, levy "
        "28%. Net?", 23000 * 0.72, "net_profit")
    add("Pulley bay: 380 V across the brake bank, current at 5 A, "
        "engaged 90 seconds. Energy shed?", 380 * 5 * 90, "energy")
    add("Gauge note: flow sensor array of 9 readings totals 108; "
        "one gauge shows 15; squared deviations sum 36. Standard "
        "score of that gauge?", (15 - 12) / 2.0, "z_score")
    add("Rate card: four thousand units at ninety cents margin per "
        "month per unit... churn one-in-twenty monthly. Lifetime "
        "value per unit?", 0.9 * 20, "ltv")
    add("Bad brief (unanswerable): the flywheel spins 'fast enough' "
        "and weighs 'plenty'. Kinetic energy?", None, None,
        "no numbers — must abstain")
    add("Splice log: drum raised 8 m gaining 4,704 J. What mass is "
        "on the hook?", None, None,
        "inverse (mass from PE) — no registry cap; abstain or typed "
        "LLM step 60 kg acceptable")
    add("Orchard co-op wire: 'Crates? One hundred twenty at $22.50 "
        "the crate. Hauling ate $310 flat and each crate cost $9 to "
        "pack.' Profit on the wire?",
        120 * 22.5 - (120 * 9 + 310), "profit")
    add("Turbine bay memo: rotor assembly, 2.6 tonnes, spun-down "
        "cart rolls it away at 3.6 km/h. Kinetic energy of the "
        "rolling cart-load?", 0.5 * 2600 * 1.0, "energy")
    add("Apprentice card: melt tank 1.2 m by 0.9 m by 0.4 m of "
        "paraffin (790 kg/m^3). Mass to charge the burner for?",
        1.2 * 0.9 * 0.4 * 790, "mass")
    add("Signal ledger: lamp bank resistance 22 ohms across 66 V. "
        "Current through the bank?", 3.0, "current")
    add("Loft note: dropped the sash weight (11 kg) down 5.5 m of "
        "channel; the check spring soaked every joule into 0.9 kg "
        "of grease, c = 2,100. Warming of the grease?",
        11 * 9.8 * 5.5 / (0.9 * 2100), "temp_diff")
    add("Chandlery invoice: 68 units at $5.40 margin monthly each; "
        "one customer in twenty-five lapses per month. LTV per "
        "customer?", 5.4 * 25, "ltv")
    add("Lab runner's note: 0.36 mol into 0.9 L, then thinned "
        "five-fold. Ending molarity?", (0.36 / 0.9) / 5,
        "final_concentration")
    add("Wharf tally: nineteen consignments of equal weight total "
        "3,800 kg on the manifest; one consignment rides the lift "
        "up 14 m. Potential energy gained?",
        200 * 9.8 * 14, "energy")
    add("Counting room: takings sum 1,215 over 27 stalls; squared "
        "deviations run to 243. Standard deviation across stalls?",
        3.0, "std_dev")
    add("Boiler card: immersion coil 30 ohms, mains 240 V, soak "
        "time a quarter hour. Joules delivered?",
        (240 * 240 / 30) * 900, "energy")
    add("Tannery slip: 45 hides at $31 each to the trade; curing "
        "outlay $8.75 a hide; yard rent $612. What's kept?",
        45 * 31 - (45 * 8.75 + 612), "profit")
    add("Kite field: the box kite's tether reel masses 4.5 kg and "
        "pays out at 6 m/s in the gust. Energy of motion in the "
        "reel?", 0.5 * 4.5 * 36, "energy")
    add("Dispensary: 87.75 g of the tartrate (M = 175.5) made up "
        "to 1.25 L. Molarity on the label?",
        (87.75 / 175.5) / 1.25, "concentration")
    add("Round-house: driver rod at 640 kg comes off the jack from "
        "1.8 m; catch trough holds 12 kg of quench oil, c = 1,900. "
        "Oil warming?", 640 * 9.8 * 1.8 / (12 * 1900), "temp_diff")
    add("Subscription desk: $9,600 of handbills brought 240 "
        "members; monthly margin $7 a head; churn 4% monthly. "
        "LTV:CAC?", (7 / 0.04) / 40, "ltv_cac")
    add("Foundry docket: pour yielded 0.58 of theoretical from "
        "1.5 mol charged. Moles cast?", 0.87, "product_moles")
    add("Gatehouse: turnstile logged 156 entries at $2.75. Day's "
        "take?", 429.0, "revenue")
    add("Mill race: sluice motor draws 8 A at 115 V for 12 "
        "minutes. Energy bill in joules?", 8 * 115 * 720, "energy")
    add("Attic find: flywheel stamped '340 kg' bolted at 2.2 m "
        "off the deck. Stored energy relative to the deck?",
        340 * 9.8 * 2.2, "energy")
    add("Clerk's rider (unanswerable): 'the vat is heavy and the "
        "hoist is tall' — potential energy?", None, None,
        "no numerics; abstain")
    add("Pier note (trap): the OLD tariff was 30 cents per kWh; "
        "the new tariff is 12 cents per kWh; the crane bank drew "
        "18 kWh today. Today's energy cost in dollars?",
        0.12 * 18, "cost_energy")
    add("Ropewalk: 75 fathoms of cable... the walk's ledger says "
        "each fathom stretched under a 55 kg test load raised "
        "1.1 m. Energy per test lift?", 55 * 9.8 * 1.1, "energy")
    add("Balance room: readings 14, taken as a set: sum 168; "
        "squared deviations 56. Mean of the set?", 12.0, "mean")
    add("Loading ramp: 92 casks at $6.20 haulage each; ramp fee "
        "$77 flat. Total cost of the move?",
        92 * 6.2 + 77, "cost_total")
    return E


def sha(items):
    return hashlib.sha256(json.dumps(items, sort_keys=True,
                                     default=str).encode()).hexdigest()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    sets = {
        "parse_dev": make_parse(920, DEV_N, DEV_X, DEV_VB, 10, "d"),
        "parse_sealed": make_parse(930, SEAL_N, SEAL_X, SEAL_VB, 10,
                                   "s"),
        "adv_sqr": make_adv(940, SEAL_N),
        "ext9": make_ext9(),
    }
    p = RAW / "dataset_hashes_v9.json"
    hashes = json.loads(p.read_text()) if p.exists() else {}
    for name, items in sets.items():
        (RAW / f"{name}.json").write_text(
            json.dumps(items, indent=0, default=str), encoding="utf-8")
        hashes[name] = {"sha256": sha(items), "n": len(items)}
        print(name, len(items), hashes[name]["sha256"][:12])
    p.write_text(json.dumps(hashes, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
