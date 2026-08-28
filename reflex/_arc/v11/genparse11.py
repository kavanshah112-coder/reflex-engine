# -*- coding: utf-8 -*-
"""parse11: long-horizon parser-coverage dataset (spec Sections
11-12, 16). Template x lexicon generation with FROZEN held-out
structure:

  templates: TRAIN vs HELDOUT (30%)
  lexemes  : TRAIN vs HELDOUT synonym variants
  quadrants: seenT_seenW (train traffic), seenT_unseenW,
             unseenT_seenW, unseenT_unseenW, oof (out-of-family)

Partitions: traffic 25,000 (seenT_seenW only) · validation 1,000 ·
sealed 1,000 (quadrant mix, disjoint seeds) · oov 240.
Phenomena tags A-Z recorded per item. Ground truth by capability
execution. Failure taxonomy is computed field-wise at evaluation.
"""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v3.ir import Quantity                          # noqa: E402
from v10.universe10 import build_registry10, execute10  # noqa: E402

REG = build_registry10()


def _run(caps, vals, target):
    st = dict(vals)
    for c in caps:
        spec = REG[c]
        try:
            ins = {k: Quantity(kind=k, value=st[k])
                   for k in spec["inputs"]}
        except KeyError:
            return None
        v, ok, _ = execute10(c, ins, REG)
        if not ok:
            return None
        st[spec["output"]] = v
    return st.get(target)


# ---------------------------------------------------------- lexicon
LEX = {
    "mass_verb": {"train": ["weighs", "has a mass of"],
                  "held": ["tips the scales at", "comes in at",
                           "registers"]},
    "speed_verb": {"train": ["moves at", "travels at"],
                   "held": ["barrels along at", "clocks",
                            "glides at"]},
    "obj": {"train": ["cart", "crate", "trolley", "block"],
            "held": ["gondola", "skip", "palette", "ingot"]},
    "lift_verb": {"train": ["is lifted", "is raised"],
                  "held": ["is hoisted", "gets winched up"]},
    "run_verb": {"train": ["runs for", "operates for"],
                 "held": ["keeps going for", "stays energised for"]},
    "cost_verb": {"train": ["costs", "is priced at"],
                  "held": ["retails for", "sets you back"]},
    "sell_verb": {"train": ["sell for", "go for"],
                  "held": ["fetch", "command"]},
    "dissolve_verb": {"train": ["dissolves", "stirs"],
                      "held": ["blends", "folds"]},
}


def pick(rng, key, unseen_w):
    pool = LEX[key]["held"] if unseen_w else LEX[key]["train"]
    return rng.choice(pool)


def num_fmt(rng, v, allow_verbal=True):
    """numeric surface forms: plain, verbal, scientific."""
    style = rng.random()
    if allow_verbal and style < 0.12 and float(v).is_integer() and \
            0 < v <= 20:
        words = ["zero", "one", "two", "three", "four", "five",
                 "six", "seven", "eight", "nine", "ten", "eleven",
                 "twelve", "thirteen", "fourteen", "fifteen",
                 "sixteen", "seventeen", "eighteen", "nineteen",
                 "twenty"]
        return words[int(v)]
    if style < 0.16 and v >= 1000:
        return f"{v:.2e}"
    return f"{v:g}"


# ------------------------------------------------------- templates
# each: (tid, family, train?, phenomena, fn(rng, unseen_w) ->
#        (text, caps, vals, target))
def t_ke_active(rng, uw):
    m = rng.choice([250, 600, 900, 1200, 1500])
    v = rng.choice([5, 8, 12, 15, 18])
    o = pick(rng, "obj", uw)
    txt = (f"A {o} {pick(rng, 'mass_verb', uw)} {num_fmt(rng, m)} kg "
           f"and {pick(rng, 'speed_verb', uw)} {num_fmt(rng, v)} "
           f"m/s. What is its kinetic energy?")
    return txt, ["kinetic_energy"], {"mass": m, "speed": v}, "energy"


def t_ke_passive(rng, uw):
    m = rng.choice([300, 700, 1000, 1400])
    v = rng.choice([6, 9, 14, 16])
    o = pick(rng, "obj", uw)
    txt = (f"At {num_fmt(rng, v)} m/s the {o} is observed; a mass of "
           f"{num_fmt(rng, m)} kg is recorded for it. Kinetic "
           f"energy?")
    return txt, ["kinetic_energy"], {"mass": m, "speed": v}, "energy"


def t_pe(rng, uw):
    m = rng.choice([20, 45, 80, 120])
    h = rng.choice([3, 6, 12, 25])
    o = pick(rng, "obj", uw)
    txt = (f"A {o} of {num_fmt(rng, m)} kg {pick(rng, 'lift_verb', uw)} "
           f"{num_fmt(rng, h)} m. How much potential energy does it "
           f"gain?")
    return txt, ["potential_energy"], {"mass": m, "height": h}, \
        "energy"


def t_elec(rng, uw):
    volt = rng.choice([36, 110, 220, 400])
    res = rng.choice([4, 11, 22, 40])
    mins = rng.choice([5, 20, 45, 90])
    txt = (f"An element of {num_fmt(rng, res)} ohms sits on "
           f"{num_fmt(rng, volt)} V and {pick(rng, 'run_verb', uw)} "
           f"{num_fmt(rng, mins)} minutes. How many joules?")
    return txt, ["current_from_vr", "power_from_vi",
                 "electrical_energy"], \
        {"voltage": volt, "resistance": res, "time": mins * 60}, \
        "energy"


def t_rev(rng, uw):
    n = rng.choice([40, 120, 300, 750])
    p = rng.choice([4, 12, 27, 55])
    txt = (f"{num_fmt(rng, n)} units {pick(rng, 'sell_verb', uw)} "
           f"${num_fmt(rng, p)} each. What revenue results?")
    return txt, ["revenue_calc"], {"count": n, "price_per_unit": p}, \
        "revenue"


def t_chem(rng, uw):
    sm = rng.choice([36, 90, 117, 180])
    mm = rng.choice([18, 58.5, 90, 180])
    vol = rng.choice([1, 2, 4])
    txt = (f"A lab {pick(rng, 'dissolve_verb', uw)} "
           f"{num_fmt(rng, sm)} g of solute (molar mass "
           f"{num_fmt(rng, mm)} g/mol) into {num_fmt(rng, vol)} L. "
           f"What is the concentration?")
    return txt, ["moles_from_mass", "concentration_calc"], \
        {"solute_mass": sm, "molar_mass": mm,
         "solution_volume": vol}, "concentration"


def t_mass_density(rng, uw):
    L = rng.choice([2, 3, 5])
    W = rng.choice([1, 2, 4])
    H = rng.choice([0.1, 0.25, 0.5])
    rho = rng.choice([1000, 2400, 7800])
    txt = (f"A slab {num_fmt(rng, L)} m long, {num_fmt(rng, W)} m "
           f"wide and {num_fmt(rng, H)} m thick has density "
           f"{num_fmt(rng, rho)} kg/m^3. What does it weigh?")
    return txt, ["area_rect", "volume_box", "mass_from_density"], \
        {"length": L, "width": W, "height": H, "density": rho}, \
        "mass"


def t_percent_tax(rng, uw):
    prof = rng.choice([4000, 9000, 22000])
    tax = rng.choice([10, 20, 35])
    txt = (f"Profits of ${num_fmt(rng, prof)} are taxed at "
           f"{num_fmt(rng, tax)}%. What net profit remains?")
    return txt, ["net_profit9"], \
        {"profit": prof, "rate_tax": tax / 100.0}, "net_profit"


def t_distractor(rng, uw):
    m = rng.choice([500, 800, 1100])
    v = rng.choice([7, 11, 14])
    d = rng.choice([33, 64, 96])
    o = pick(rng, "obj", uw)
    txt = (f"A {o} {pick(rng, 'mass_verb', uw)} {num_fmt(rng, m)} kg "
           f"and {pick(rng, 'speed_verb', uw)} {num_fmt(rng, v)} "
           f"m/s. The depot brochure is rated for {d} passes. "
           f"Kinetic energy?")
    return txt, ["kinetic_energy"], {"mass": m, "speed": v}, "energy"


def t_two_entity(rng, uw):
    m1, v1 = rng.choice([(900, 8), (1200, 12)])
    m2, v2 = rng.choice([(700, 15), (1000, 18)])
    txt = (f"Cart A {pick(rng, 'mass_verb', uw)} {num_fmt(rng, m1)} "
           f"kg and {pick(rng, 'speed_verb', uw)} {num_fmt(rng, v1)} "
           f"m/s. Cart B {pick(rng, 'mass_verb', uw)} "
           f"{num_fmt(rng, m2)} kg and {pick(rng, 'speed_verb', uw)} "
           f"{num_fmt(rng, v2)} m/s. What is the kinetic energy of "
           f"the faster cart?")
    tgt = (m2, v2) if v2 > v1 else (m1, v1)
    return txt, ["kinetic_energy"], \
        {"mass": tgt[0], "speed": tgt[1]}, "energy"


def t_temporal(rng, uw):
    m1 = rng.choice([40, 80, 120])
    m2 = m1 - rng.choice([5, 15, 25])
    txt = (f"Initially the vat holds {num_fmt(rng, m1)} kg; finally "
           f"it holds {num_fmt(rng, m2)} kg. How much mass was "
           f"lost?")
    return txt, None, {"__delta__": m1 - m2}, "mass"


def t_fraction(rng, uw):
    n = rng.choice([200, 480, 900])
    p = rng.choice([2.5, 7.5, 12.5])
    txt = (f"Each of {num_fmt(rng, n)} pieces {pick(rng, 'sell_verb', uw)} "
           f"${p} apiece. Revenue?")
    return txt, ["revenue_calc"], {"count": n, "price_per_unit": p}, \
        "revenue"


def t_reorder(rng, uw):
    volt = rng.choice([48, 230])
    res = rng.choice([6, 16])
    txt = (f"For an element on {num_fmt(rng, volt)} V — its "
           f"resistance being {num_fmt(rng, res)} ohms — what "
           f"current flows?")
    return txt, ["current_from_vr"], \
        {"voltage": volt, "resistance": res}, "current"


TEMPLATES = [
    ("ke_active", True, "AB", t_ke_active),
    ("pe", True, "AB", t_pe),
    ("elec", True, "AQ", t_elec),
    ("rev", True, "AR", t_rev),
    ("chem", True, "AQ", t_chem),
    ("mass_density", True, "AL", t_mass_density),
    ("percent_tax", True, "S", t_percent_tax),
    ("distractor", True, "M", t_distractor),
    ("two_entity", True, "KO", t_two_entity),
    ("fraction", True, "R", t_fraction),
    # held-out templates (never in traffic)
    ("ke_passive", False, "GX", t_ke_passive),
    ("temporal", False, "OX", t_temporal),
    ("reorder", False, "FX", t_reorder),
]


def make_item(rng, tid, fam_train, phen, fn, unseen_w, split, idx):
    for _ in range(30):
        txt, caps, vals, target = fn(rng, unseen_w)
        if caps is None:
            ans = vals["__delta__"]
        else:
            ans = _run(caps, vals, target)
        if ans is not None:
            quad = (("seenT" if fam_train else "unseenT") + "_" +
                    ("unseenW" if unseen_w else "seenW"))
            return {"id": f"p11{split[0]}{idx:05d}", "q": txt,
                    "answer": ans, "template": tid,
                    "phenomena": phen, "quadrant": quad,
                    "target_kind": target}
    return None


def _sha(items):
    return hashlib.sha256(json.dumps(items, sort_keys=True,
                                     default=str).encode()).hexdigest()


def gen_traffic(n=25000, seed=1111):
    rng = random.Random(seed)
    train_t = [t for t in TEMPLATES if t[1]]
    items = []
    while len(items) < n:
        tid, ft, ph, fn = train_t[len(items) % len(train_t)]
        it = make_item(rng, tid, ft, ph, fn, False, "traffic",
                       len(items))
        if it:
            items.append(it)
    return items


def gen_eval(split, seed, n):
    rng = random.Random(seed)
    items = []
    # quadrant mix: 40% seenT_seenW, 20% seenT_unseenW,
    # 20% unseenT_seenW, 20% unseenT_unseenW
    mix = ([("tr", False)] * 4 + [("tr", True)] * 2 +
           [("hd", False)] * 2 + [("hd", True)] * 2)
    tr = [t for t in TEMPLATES if t[1]]
    hd = [t for t in TEMPLATES if not t[1]]
    while len(items) < n:
        kind, uw = mix[len(items) % len(mix)]
        pool = tr if kind == "tr" else hd
        tid, ft, ph, fn = rng.choice(pool)
        it = make_item(rng, tid, ft, ph, fn, uw, split, len(items))
        if it:
            items.append(it)
    return items


OOF = [
    # out-of-family phrasings (hand-written), answers analytic
    ("Nine hundred kilograms of rolling stock at a dozen metres per "
     "second — kinetic energy?", 0.5 * 900 * 144),
    ("Take a 2-tonne flywheel doing 10 m/s; how many joules of "
     "motion does it hold?", 0.5 * 2000 * 100),
    ("Lifting sixty kilos through four metres banks how much "
     "potential energy?", 60 * 9.8 * 4),
    ("An 11-ohm coil across 110 volts: the current, please.", 10.0),
    ("Two hundred fifty widgets at nine dollars each - the take?",
     2250.0),
    ("A brick of 2 by 1 by 0.1 metres in 7800 kg/m^3 steel weighs "
     "what?", 2 * 1 * 0.1 * 7800),
]


def gen_oof(seed=4444, n=240):
    rng = random.Random(seed)
    items = []
    # hand-written stems recycled with numeric perturbation via the
    # held-out templates in unseen-word mode + the literal OOF list
    hd = [t for t in TEMPLATES if not t[1]]
    for i, (q, a) in enumerate(OOF):
        items.append({"id": f"p11o{i:05d}", "q": q, "answer": a,
                      "template": "oof_hand", "phenomena": "Z",
                      "quadrant": "oof", "target_kind": None})
    while len(items) < n:
        tid, ft, ph, fn = rng.choice(hd)
        it = make_item(rng, tid, ft, ph, fn, True, "oofx",
                       len(items))
        if it:
            it["quadrant"] = "oof"
            items.append(it)
    return items


def main():
    out = ROOT / "results/raw_v11"
    out.mkdir(parents=True, exist_ok=True)
    hp = out / "dataset_hashes_v11.json"
    hashes = json.loads(hp.read_text(encoding="utf-8")) \
        if hp.exists() else {}
    tr = gen_traffic()
    (out / "parse11_traffic.json").write_text(
        json.dumps(tr), encoding="utf-8")
    hashes["parse11_traffic"] = {"sha256": _sha(tr), "n": len(tr)}
    for split, seed, n in (("val", 2222, 1000),
                           ("sealed", 3333, 1000)):
        items = gen_eval(split, seed, n)
        (out / f"parse11_{split}.json").write_text(
            json.dumps(items, indent=1), encoding="utf-8")
        hashes[f"parse11_{split}"] = {"sha256": _sha(items),
                                      "n": len(items)}
    oof = gen_oof()
    (out / "parse11_oof.json").write_text(
        json.dumps(oof, indent=1), encoding="utf-8")
    hashes["parse11_oof"] = {"sha256": _sha(oof), "n": len(oof)}
    hp.write_text(json.dumps(hashes, indent=1), encoding="utf-8")
    for k in hashes:
        print(k, hashes[k]["n"], hashes[k]["sha256"][:10])


if __name__ == "__main__":
    main()
