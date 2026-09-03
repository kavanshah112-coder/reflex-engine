# -*- coding: utf-8 -*-
# origin: new for V1.7 -- the Q-1M composition workload builder (SPEC 5)
"""1,000,000 items where every in-domain item is a CHAIN: a plan DAG
of 2-6 steps whose gold is the independent chain witness's replay of
that plan. No engine code touches a gold.

  python tools/build_q1m.py --n 1000000 [--out results/v17/data]

Per item (JSONL):
  {id, text, plan, gold, gold_type, k, leaves, nonmono, multidomain,
   register, distractor, sig}

Frozen recipe (v1.7-plan AMENDMENT): depth mix k=2:20/3:30/4:25/
5:15/6:10; >=40%% multi-domain; >=50%% non-monotone at k>=3;
distractors = the unique GSM8K+ASDiv corpus (~3.6k; the spec's 2%%
is capped by supply -- recorded in the manifest); ~6k foreign slots
(bridge-authored later, fact sheets fixed here). Splits ACQ 200k /
DEV 100k / SEAL 300k / REPLAY 400k, distractors disjoint.

Determinism: seed 1700; identical output on re-run. Golds verified
at build: every item's stored gold IS replay(plan) and a second
replay must agree (a flaky chain is rejected).
"""
import argparse
import json
import math
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tools"))
import chain_witness17 as CW  # noqa: E402
from reflex import planschema17 as PS  # noqa: E402

SEED = 1700

L = {
    "root": "mathematics/algebra/quadratic_polynomial_solve",
    "deriv": "mathematics/calculus/differentiation/evaluate_at_point",
    "integ": "mathematics/calculus/integration/definite",
    "gcd": "mathematics/number_theory/gcd_lcm",
    "ncr": "mathematics/combinatorics_probability/"
           "permutations_combinations",
    "sum": "mathematics/sequences_series/finite_sum",
    "eval": "mathematics/arithmetic/expression_evaluation",
    "conv": "units_conversion/simple_units",
    "convr": "units_conversion/compound_rates",
    "ke": "physics/mechanics/energy_work",
    "force": "physics/mechanics/dynamics_forces",
    "pe": "physics/mechanics/energy_work",
    "ohm": "physics/electricity/dc_circuits",
    "si": "quantitative_finance/interest_growth",
    "profit": "quantitative_finance/profitability",
    "cmp": "logic/comparison_ordering",
}


# ---------------------------------------------------------------------
# START steps: (node builder, text templates, leaf, value range hint)
# ---------------------------------------------------------------------
def start_root(rng):
    r1, r2 = rng.sample(range(1, 9), 2)
    b, c = -(r1 + r2), r1 * r2
    lhs = ("x**2 %+d*x %+d" % (b, c)).replace("+ -", "- ")
    disp = lhs.replace("**", "^").replace("*", "")
    pick = rng.choice(["larger", "smaller"])
    node = {"op": "solve_pick", "lhs": lhs, "pick": pick}
    txt = rng.choice([
        "Take the %s root of %s = 0" % (pick, disp),
        "Find the %s root of %s = 0" % (pick, disp),
        "Start with the %s root of %s = 0" % (pick, disp),
    ])
    return node, txt, L["root"]


def start_deriv(rng):
    c3, c2 = rng.randint(1, 5), rng.randint(-6, 6)
    expr = "%d*x**3 %+d*x**2" % (c3, c2)
    disp = expr.replace("**", "^").replace("*", "")
    pt = rng.randint(1, 4)
    order = rng.choice([1, 1, 2])
    ow = {1: "first", 2: "second"}[order]
    node = {"op": "derivative_at", "expr": expr, "order": order,
            "point": float(pt)}
    txt = rng.choice([
        "Take the %s derivative of %s at x = %d" % (ow, disp, pt),
        "Compute the %s derivative of %s at x = %d" % (ow, disp, pt),
    ])
    return node, txt, L["deriv"]


def start_integ(rng):
    c2, c1 = rng.randint(1, 5), rng.randint(0, 8)
    expr = "%d*x**2 %+d*x" % (c2, c1)
    disp = expr.replace("**", "^").replace("*", "")
    a, b = sorted(rng.sample(range(0, 5), 2))
    node = {"op": "integrate_def", "expr": expr, "a": a, "b": b}
    txt = rng.choice([
        "Find the integral of %s from %d to %d" % (disp, a, b),
        "Take the integral of %s from %d to %d" % (disp, a, b),
    ])
    return node, txt, L["integ"]


def start_gcd(rng):
    a, b = rng.randint(12, 400), rng.randint(12, 400)
    op = rng.choice(["gcd", "lcm"])
    name = {"gcd": rng.choice(["gcd", "greatest common divisor"]),
            "lcm": rng.choice(["lcm", "least common multiple"])}[op]
    node = {"op": op, "a": a, "b": b}
    txt = "Compute the %s of %d and %d" % (name, a, b)
    return node, txt, L["gcd"]


def start_ncr(rng):
    n = rng.randint(6, 20)
    r = rng.randint(2, 4)
    node = {"op": "ncr", "n": n, "r": r}
    txt = rng.choice(["Compute %d choose %d" % (n, r),
                      "Take %d choose %d" % (n, r)])
    return node, txt, L["ncr"]


def start_sum(rng):
    e = rng.choice(["k", "k**2", "2*k - 1"])
    n = rng.randint(4, 25)
    node = {"op": "sum_finite", "expr": e, "var": "k", "a": 1, "b": n}
    disp = e.replace("**", "^").replace("*", "")
    txt = "Compute the sum of %s for k = 1 to %d" % (disp, n)
    return node, txt, L["sum"]


def start_eval(rng):
    a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(1, 20)
    expr = "%d*(%d + %d)" % (a, b, c)
    node = {"op": "evaluate", "expr": expr}
    txt = rng.choice(["Compute %d(%d + %d)" % (a, b, c),
                      "Start with %d*(%d + %d)" % (a, b, c)])
    return node, txt, L["eval"]


STARTS = [start_root, start_deriv, start_integ, start_gcd,
          start_ncr, start_sum, start_eval]


# ---------------------------------------------------------------------
# MIDDLE steps: consume "@prev" -> numeric out
# fam tags drive the non-monotone flag (consecutive same fam = mono)
# ---------------------------------------------------------------------
def mid_scale(rng, ref, state):
    f = rng.randint(2, 12)
    node = {"op": "scale", "value": "@" + ref, "by": float(f)}
    txt = rng.choice(["Multiply that by %d" % f,
                      "Multiply the result by %d" % f])
    return node, txt, L["eval"], "arith", state["v"] * f, state["u"]


def mid_add(rng, ref, state):
    a = rng.randint(1, 30)
    if rng.random() < 0.5:
        node = {"op": "evaluate", "expr": "@%s + %d" % (ref, a)}
        txt = "Add %d to that" % a
        nv = state["v"] + a
    else:
        node = {"op": "evaluate", "expr": "@%s - %d" % (ref, a)}
        txt = "Subtract %d from that" % a
        nv = state["v"] - a
    return node, txt, L["eval"], "arith", nv, state["u"]


def mid_ke(rng, ref, state):
    m = rng.randint(2, 60)
    node = {"op": "formula", "expr": "0.5 * m * v**2", "m": float(m),
            "v": "@" + ref, "unit": "J"}
    txt = ("Using that as the speed in m/s of a %d kg mass, find "
           "the kinetic energy" % m)
    return (node, txt, L["ke"], "physics",
            0.5 * m * state["v"] ** 2, "J")


def mid_force(rng, ref, state):
    m = rng.randint(2, 200)
    node = {"op": "formula", "expr": "m * a", "m": float(m),
            "a": "@" + ref, "unit": "N"}
    txt = ("Using that as the acceleration in m/s^2 of a %d kg "
           "mass, find the force" % m)
    return node, txt, L["force"], "physics", m * state["v"], "N"


def mid_si(rng, ref, state):
    r, t = rng.randint(2, 9), rng.randint(2, 8)
    node = {"op": "formula", "expr": "p * r * t / 100",
            "p": "@" + ref, "r": float(r), "t": float(t), "unit": "$"}
    txt = ("Using that as a principal in dollars, find the simple "
           "interest at %d%% per year over %d years" % (r, t))
    return (node, txt, L["si"], "finance",
            state["v"] * r * t / 100.0, "$")


def mid_conv(rng, ref, state):
    table = {"J": [("kJ", 0.001, L["conv"])],
             "m/s": [("km/h", 3.6, L["convr"])],
             "N": [("kN", 0.001, L["conv"])],
             None: [("kJ", None, None)]}
    opts = table.get(state["u"])
    if not opts or opts[0][1] is None:
        return None
    to, fac, leaf = opts[0]
    node = {"op": "convert", "value": "@" + ref,
            "from": state["u"], "to": to}
    txt = rng.choice(["Express the result in %s from %s"
                      % (to, state["u"]),
                      "Convert that to %s from %s"
                      % (to, state["u"])])
    return node, txt, leaf, "units", state["v"] * fac, to


MIDS = [mid_scale, mid_add, mid_ke, mid_force, mid_si, mid_conv]
# which mids are sensible given current unit/magnitude
def _mid_ok(fn, state):
    v, u = state["v"], state["u"]
    if fn is mid_conv:
        return u in ("J", "m/s", "N")
    if fn in (mid_ke, mid_force):
        return u is None and 0 < v <= 80
    if fn is mid_si:
        return u in (None, "$") and 10 <= v <= 1e6
    if fn is mid_scale or fn is mid_add:
        return abs(v) < 1e9
    return True


def gen_item(rng, k):
    """One chain item of node-count k. Returns dict or None."""
    sf = STARTS[rng.randrange(len(STARTS))]
    node, txt, leaf = sf(rng)
    node = dict(node)
    node["id"] = "n1"
    nodes = [node]
    texts = [txt]
    leaves = [leaf]
    fams = ["start"]
    # forward value estimate via witness single replay later; keep a
    # rough tracker for parameter sanity by replaying incrementally
    try:
        v0, _, _ = CW.replay({"nodes": nodes, "final": "n1"})
    except CW.ChainRefuse:
        return None
    state = {"v": v0, "u": ("J" if sf is start_integ and False
                            else None)}
    threshold_final = k >= 4 and rng.random() < 0.15
    body = k - 1 - (1 if threshold_final else 0)
    for i in range(body):
        cands = [fn for fn in MIDS if _mid_ok(fn, state)]
        if not cands:
            return None
        fn = cands[rng.randrange(len(cands))]
        out = fn(rng, nodes[-1]["id"], state)
        if out is None:
            return None
        nd, t, lf, fam, nv, nu = out
        nd = dict(nd)
        nd["id"] = "n%d" % (len(nodes) + 1)
        nodes.append(nd)
        texts.append(t)
        leaves.append(lf)
        fams.append(fam)
        state = {"v": nv, "u": nu}
    gold_type = "num"
    if threshold_final:
        thr = round(state["v"] * rng.choice([0.5, 0.8, 1.2, 2.0]), 2)
        nd = {"id": "n%d" % (len(nodes) + 1), "op": "compare",
              "a": "@" + nodes[-1]["id"], "b": float(thr)}
        nodes.append(nd)
        texts.append("Is the final value greater than %g" % thr)
        leaves.append(L["cmp"])
        fams.append("logic")
        gold_type = "bool"
    plan = {"nodes": nodes, "final": nodes[-1]["id"]}
    try:
        gold, kk, _fd = CW.replay(plan)
        gold2, _, _ = CW.replay(plan)
    except CW.ChainRefuse:
        return None
    if abs(gold - gold2) > 1e-9 * (1 + abs(gold)):
        return None
    if not math.isfinite(gold) or abs(gold) > 1e12:
        return None
    if gold_type == "bool":
        gold = bool(gold > 0)
    text = ". ".join(texts) + ("?" if gold_type == "bool" else ".")
    if state["u"] and gold_type == "num":
        # name the answer unit in the ask ~half the time
        if rng.random() < 0.5:
            text = text[:-1] + ", in %s." % state["u"]
    nonmono = any(a != b for a, b in zip(fams[1:-1], fams[2:])) \
        if len(fams) > 2 else False
    doms = {lf.split("/")[0] for lf in leaves}
    return {"text": text, "plan": plan, "gold": gold,
            "gold_type": gold_type, "k": len(nodes),
            "leaves": leaves, "nonmono": bool(nonmono),
            "multidomain": len(doms) > 1,
            "register": "own", "distractor": False,
            "sig": PS.signature(plan)}


def load_distractors():
    out = []
    p = HERE / "corpora" / "gsm8k_test.jsonl"
    for i, line in enumerate(p.read_text(encoding="utf-8")
                             .splitlines()):
        if not line.strip():
            continue
        d = json.loads(line)
        out.append({"text": d["question"],
                    "gold": d["answer"].split("####")[-1].strip()
                    .replace(",", ""), "sid": "g%04d" % i})
    x = ET.parse(HERE / "corpora" / "asdiv.xml").getroot()
    for i, pr in enumerate(x.iter("Problem")):
        body = (pr.findtext("Body") or "").strip()
        q = (pr.findtext("Question") or "").strip()
        if body and q:
            out.append({"text": "%s %s" % (body, q),
                        "gold": (pr.findtext("Answer") or "").strip(),
                        "sid": "a%04d" % i})
    return out


K_MIX = [(2, 0.20), (3, 0.30), (4, 0.25), (5, 0.15), (6, 0.10)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000000)
    ap.add_argument("--out", default=str(HERE / "results" / "v17" /
                                         "data"))
    a = ap.parse_args()
    rng = random.Random(SEED)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    distr = load_distractors()
    rng.shuffle(distr)
    n_total = a.n
    n_dist = min(len(distr), round(n_total * 0.02))
    n_foreign = round(n_total * 0.006) if n_total >= 100000 else 0
    n_prog = n_total - n_dist

    quota = {k: round(n_prog * f) for k, f in K_MIX}
    quota[3] += n_prog - sum(quota.values())
    made = {k: 0 for k in quota}
    items, rejects, idx = [], 0, 0
    while sum(made.values()) < n_prog:
        k = next(kk for kk, _f in K_MIX if made[kk] < quota[kk])
        it = gen_item(rng, k)
        if it is None:
            rejects += 1
            if rejects > n_prog:
                raise RuntimeError("generator reject rate too high")
            continue
        it["id"] = "q17_%07d" % idx
        idx += 1
        items.append(it)
        made[k] += 1
        if idx % 100000 == 0:
            print("generated", idx, flush=True)
    for i in rng.sample(range(len(items)), n_foreign):
        items[i]["register"] = "foreign_slot"
    for j, d in enumerate(distr[:n_dist]):
        items.append({"id": "q17_dist_%04d" % j, "text": d["text"],
                      "plan": None, "gold": d["gold"],
                      "gold_type": "num", "k": None, "leaves": [],
                      "nonmono": False, "multidomain": False,
                      "register": "corpus", "distractor": True,
                      "sig": None})
    rng.shuffle(items)

    n = len(items)
    cuts = [int(n * 0.2), int(n * 0.3), int(n * 0.6)]
    splits = {"acq": items[:cuts[0]],
              "dev": items[cuts[0]:cuts[1]],
              "seal": items[cuts[1]:cuts[2]],
              "replay": items[cuts[2]:]}
    for name, part in splits.items():
        with open(out / ("q1m_%s.jsonl" % name), "w",
                  encoding="utf-8") as f:
            for it in part:
                f.write(json.dumps(it) + "\n")
    nm = sum(1 for i in items if i.get("nonmono"))
    md = sum(1 for i in items if i.get("multidomain"))
    manifest = {"seed": SEED, "n": n, "programmatic": n_prog,
                "foreign_slots": n_foreign, "distractors": n_dist,
                "distractor_note": "2% capped by unique corpus "
                                   "supply" if n_dist < round(
                                       n_total * 0.02) else "2%",
                "rejects": rejects, "k_quota": quota,
                "nonmono_share": round(nm / max(1, n_prog), 4),
                "multidomain_share": round(md / max(1, n_prog), 4),
                "splits": {k: len(v) for k, v in splits.items()}}
    (out / "q1m_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
