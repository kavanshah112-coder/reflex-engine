# -*- coding: utf-8 -*-
# origin: new for V1.6 -- generates the frozen taxonomy artifact (SPEC 5.1)
"""Builds taxonomy.json: the tree + the capability map.

Run once before plan-freeze evaluation begins; the committed output is
the frozen artifact. Regenerating must be byte-stable (sorted keys, no
timestamps) so `python tools/gen_taxonomy16.py --check` can verify the
committed file was produced by this script and that every capability
in packs/physics/caps.json has exactly one address.

Executors:
  tierA     -- the existing certified engine (V1.0-V1.2 line)
  symcore16 -- the V1.6 symbolic core (SPEC 5.3; nothing served from
               these leaves without the numeric cross-check gate)
Leaves with executor symcore16 exist in the tree from freeze so minted
reflexes and Q-100K items have addresses, but no query is served from
them until GATE-CTRL passes.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- tree
# node: {children: {...}} internal | {executor: ...} leaf
def L(executor):
    return {"executor": executor}

TREE = {
    "mathematics": {
        "arithmetic": {
            "integer_rational_ops": L("tierA"),
            "percentages_ratios": L("tierA"),
            "expression_evaluation": L("symcore16"),
        },
        "algebra": {
            "linear_solve": L("symcore16"),
            "quadratic_polynomial_solve": L("symcore16"),
            "rearrangement_substitution": L("symcore16"),
        },
        "calculus": {
            "differentiation": {
                "first_derivative": L("symcore16"),
                "second_derivative": L("symcore16"),
                "higher_order": L("symcore16"),
                "evaluate_at_point": L("symcore16"),
            },
            "integration": {
                "indefinite": L("symcore16"),
                "definite": L("symcore16"),
            },
            "limits": {
                "finite_point": L("symcore16"),
                "at_infinity": L("symcore16"),
            },
        },
        "geometry_mensuration": {
            "area_perimeter": L("tierA"),
            "volume_surface": L("tierA"),
        },
        "trigonometry": {
            "evaluation": L("symcore16"),
            "identities_simplify": L("symcore16"),
        },
        "sequences_series": {
            "arithmetic_geometric": L("symcore16"),
            "finite_sum": L("symcore16"),
        },
        "number_theory": {
            "gcd_lcm": L("symcore16"),
            "divisibility_primes": L("symcore16"),
        },
        "combinatorics_probability": {
            "permutations_combinations": L("symcore16"),
            "basic_probability": L("symcore16"),
        },
        "statistics": {
            "descriptive": L("tierA"),
            "standardized_scores": L("tierA"),
        },
    },
    "physics": {
        "mechanics": {
            "dynamics_forces": L("tierA"),
            "energy_work": L("tierA"),
            "mass_density_weight": L("tierA"),
            "kinematics": L("symcore16"),
        },
        "electricity": {
            "dc_circuits": L("tierA"),
            "electrical_energy_power": L("tierA"),
        },
        "thermodynamics": {
            "heat_temperature": L("tierA"),
            "engines_efficiency": L("tierA"),
        },
        "waves_optics": {
            "wave_relations": L("symcore16"),
        },
    },
    "chemistry_quantitative": {
        "solution_stoichiometry": L("tierA"),
        "gas_laws": L("symcore16"),
    },
    "quantitative_finance": {
        "cost_revenue": L("tierA"),
        "profitability": L("tierA"),
        "unit_economics": L("tierA"),
        "interest_growth": L("tierA"),
    },
    "units_conversion": {
        "simple_units": L("tierA"),
        "compound_rates": L("tierA"),
    },
    "logic": {
        "propositional_evaluation": L("symcore16"),
        "set_operations": L("symcore16"),
        "boolean_algebra": L("symcore16"),
        "comparison_ordering": L("symcore16"),
    },
}

# ------------------------------------------- capability -> leaf address
# Every capability in packs/physics/caps.json maps to EXACTLY one leaf.
# The address is evidence-checkable: the cap's dimensional signature
# must be consistent with its leaf's domain (validated by taxonomy16).
CAP_MAP = {
    # finance: profitability
    "annual_profit_calc": "quantitative_finance/profitability",
    "cycle_profit_from_margin": "quantitative_finance/profitability",
    "margin_calc": "quantitative_finance/profitability",
    "margin_net": "quantitative_finance/profitability",
    "margin_of_unit": "quantitative_finance/profitability",
    "monthly_profit_calc": "quantitative_finance/profitability",
    "net_profit9": "quantitative_finance/profitability",
    "payback_calc": "quantitative_finance/profitability",
    "per_unit_profit": "quantitative_finance/profitability",
    "profit_calc": "quantitative_finance/profitability",
    "roi_calc": "quantitative_finance/profitability",
    # finance: cost / revenue
    "break_even": "quantitative_finance/cost_revenue",
    "energy_cost": "quantitative_finance/cost_revenue",
    "material_cost": "quantitative_finance/cost_revenue",
    "operating_cost": "quantitative_finance/cost_revenue",
    "paint_cost": "quantitative_finance/cost_revenue",
    "revenue_calc": "quantitative_finance/cost_revenue",
    "revenue_sale": "quantitative_finance/cost_revenue",
    "total_cost": "quantitative_finance/cost_revenue",
    "total_cost9": "quantitative_finance/cost_revenue",
    "variable_cost": "quantitative_finance/cost_revenue",
    # finance: unit economics
    "cac_calc": "quantitative_finance/unit_economics",
    "lifetime_from_churn": "quantitative_finance/unit_economics",
    "ltv_cac_ratio": "quantitative_finance/unit_economics",
    "ltv_calc": "quantitative_finance/unit_economics",
    # finance: interest / growth (incl. the two V1.0-bred reflexes)
    "bred_final_amount": "quantitative_finance/interest_growth",
    "bred_money": "quantitative_finance/interest_growth",
    "interest_from_final": "quantitative_finance/interest_growth",
    "simple_interest": "quantitative_finance/interest_growth",
    # chemistry
    "concentration_calc": "chemistry_quantitative/solution_stoichiometry",
    "dilute": "chemistry_quantitative/solution_stoichiometry",
    "moles_from_mass": "chemistry_quantitative/solution_stoichiometry",
    "yield_product": "chemistry_quantitative/solution_stoichiometry",
    # electricity
    "charge_from_it": "physics/electricity/dc_circuits",
    "current_from_vr": "physics/electricity/dc_circuits",
    "voltage_from_ir": "physics/electricity/dc_circuits",
    "power_from_i2r": "physics/electricity/electrical_energy_power",
    "power_from_vi": "physics/electricity/electrical_energy_power",
    "electrical_energy": "physics/electricity/electrical_energy_power",
    # mechanics
    "force_from_mass_accel": "physics/mechanics/dynamics_forces",
    "work_from_force": "physics/mechanics/energy_work",
    "kinetic_energy": "physics/mechanics/energy_work",
    "potential_energy": "physics/mechanics/energy_work",
    "height_from_energy": "physics/mechanics/energy_work",
    "speed_from_energy": "physics/mechanics/energy_work",
    "energy_conservation": "physics/mechanics/energy_work",
    "mass_from_density": "physics/mechanics/mass_density_weight",
    "weight_from_mass": "physics/mechanics/mass_density_weight",
    # engineering geometry
    "area_rect": "mathematics/geometry_mensuration/area_perimeter",
    "volume_box": "mathematics/geometry_mensuration/volume_surface",
    # statistics
    "mean_calc": "mathematics/statistics/descriptive",
    "std_calc": "mathematics/statistics/descriptive",
    "variance_calc": "mathematics/statistics/descriptive",
    "z_calc": "mathematics/statistics/standardized_scores",
    # thermodynamics
    "heat_to_temp_rise": "physics/thermodynamics/heat_temperature",
    "temp_rise_to_heat": "physics/thermodynamics/heat_temperature",
    "carnot_efficiency": "physics/thermodynamics/engines_efficiency",
    "work_from_heat_eff": "physics/thermodynamics/engines_efficiency",
}


def leaves(tree, prefix=""):
    out = {}
    for k, v in tree.items():
        path = "%s/%s" % (prefix, k) if prefix else k
        if "executor" in v:
            out[path] = v["executor"]
        else:
            out.update(leaves(v, path))
    return out


def build():
    lf = leaves(TREE)
    caps = json.loads(
        (HERE / "packs" / "physics" / "caps.json").read_text(encoding="utf-8"))
    # every capability has exactly one address, and it is a real leaf
    missing = sorted(set(caps) - set(CAP_MAP))
    extra = sorted(set(CAP_MAP) - set(caps))
    bad = sorted(p for p in CAP_MAP.values() if p not in lf)
    assert not missing, "unmapped capabilities: %s" % missing
    assert not extra, "mapped but nonexistent capabilities: %s" % extra
    assert not bad, "addresses that are not leaves: %s" % bad
    # existing caps only ever map to tierA leaves (nothing served from
    # symcore16 leaves until GATE-CTRL passes)
    wrong_exec = sorted(c for c, p in CAP_MAP.items() if lf[p] != "tierA")
    assert not wrong_exec, "caps mapped to non-tierA leaves: %s" % wrong_exec
    return {
        "version": "v1.6-plan",
        "tree": TREE,
        "leaves": {p: lf[p] for p in sorted(lf)},
        "capability_map": {c: CAP_MAP[c] for c in sorted(CAP_MAP)},
        "counts": {
            "leaves": len(lf),
            "tierA_leaves": sum(1 for e in lf.values() if e == "tierA"),
            "symcore16_leaves": sum(
                1 for e in lf.values() if e == "symcore16"),
            "capabilities_mapped": len(CAP_MAP),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify committed taxonomy.json matches")
    a = ap.parse_args()
    doc = build()
    text = json.dumps(doc, indent=1, sort_keys=False)
    out = HERE / "taxonomy.json"
    if a.check:
        committed = out.read_text(encoding="utf-8").replace("\r\n", "\n")
        if committed != text:
            print("MISMATCH: committed taxonomy.json != generator output")
            sys.exit(1)
        print("taxonomy.json verified:", doc["counts"])
        return
    out.write_text(text, encoding="utf-8")
    print("taxonomy.json written:", doc["counts"])


if __name__ == "__main__":
    main()
