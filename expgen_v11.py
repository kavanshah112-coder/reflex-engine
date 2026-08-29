# -*- coding: utf-8 -*-
# origin: new for V1.1 — pre-registered generators (V1_1_SPEC §3, §7)
"""V1.1 dataset generation (G1 residual v2, G2 commercial 25k,
G3 finals). COMMITTED BEFORE RUNNING; run exactly once.

AMENDMENT A (pre-data, recorded): the spec's G1 sizes (val 1000 /
traffic 5000 / sealed 500) assumed a post-fix residual rate near
V1.0's 16.6%. Measured on a dev sizing sample: 1.3% (44/3500, zero
wrong), concentrated in ~2 template families. 6,500 residual items
would need a ~500k pool of near-clones. G1 resized to the real
frontier: pool 160,000 parse + 20,000 oof; splits val 300 / traffic
2,000 / sealed 300 (loud-fail below 2,600 residuals). Seeds, filter,
and split logic unchanged. Family concentration is reported, not
hidden (no silent caps).

G2 commercial stream (25,000, varied topics, natural mix):
  82% physics/electrical/thermo/finance/maths via the v0.11-recipe
  eval generator (all quadrants — realistic difficulty mix);
  10% fact-recall (frozen materials table; 60% STATING the constant,
  40% OMITTING it — the MEMORY.fact use case; ground truth from the
  table);
  8% definition/lookup (20 frozen questions x ~100 occurrences;
  numeric lookups graded by tolerance, text answers graded by
  required-keyword sets — the TEXT.qa use case).
G3: 600 mixed sim finals (same weights, fresh seed) + fresh sem/adv
integrity finals (v0.11 recipes).
"""
import hashlib
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))

OUT = HERE / "results" / "expacq11" / "data"

G1_PARSE_SEED, G1_PARSE_N = 8555, 160000
G1_OOF_SEED, G1_OOF_N = 8556, 20000
G1_SHUFFLE = 8557
G1_VAL, G1_TRAFFIC, G1_SEALED = 300, 2000, 300
# AMENDMENT B (user-directed, pre-data): commercial sim scaled to
# 100,000 queries; W1b engine fixes precede G1 filtering
G2_SEED, G2_N = 9555, 100000
G3_SEED, SEM_SEED, ADV_SEED = 9666, 9777, 9778

MATERIALS = {  # material -> density kg/m^3 (frozen ground truth)
    "steel": 7800.0, "aluminium": 2700.0, "copper": 8960.0,
    "concrete": 2400.0, "oak": 750.0, "glass": 2500.0,
    "brass": 8500.0, "granite": 2650.0,
}
FACT_STATING = [
    "A {m} ingot with density {d} kg/m^3 and volume {v} m^3 - mass?",
    "The {m} block ({d} kg/m^3) measures {v} m^3; what does it weigh?",
    "Density of this {m} piece is {d} kg/m^3, volume {v} m^3. Mass?",
]
FACT_OMITTING = [
    "A {m} block of volume {v} m^3 - what mass?",
    "What does a {v} m^3 chunk of {m} weigh?",
    "A solid {m} casting, {v} m^3 in volume; its mass?",
]
DEFINITIONS = [  # (question, numeric answer OR keyword list)
    ("At what Celsius temperature does water boil at sea level?",
     100.0),
    ("At what Celsius temperature does water freeze?", 0.0),
    ("How many seconds are there in an hour?", 3600.0),
    ("How many metres are in one kilometre?", 1000.0),
    ("How many grams make one kilogram?", 1000.0),
    ("How many joules is one kilowatt-hour?", 3.6e6),
    ("How many millilitres are in a litre?", 1000.0),
    ("What is standard gravitational acceleration in m/s^2?", 9.8),
    ("How many watts is one kilowatt?", 1000.0),
    ("How many minutes are in a day?", 1440.0),
    ("State Ohm's law.", ["voltage", "current", "resistance"]),
    ("State Newton's second law.", ["force", "mass", "acceleration"]),
    ("What is kinetic energy proportional to?",
     ["mass", "speed"]),
    ("What does power measure?", ["energy", "time"]),
    ("What is density defined as?", ["mass", "volume"]),
    ("What does Hooke's law relate?", ["force", "extension"]),
    ("What is electrical power in terms of voltage and current?",
     ["voltage", "current"]),
    ("What quantity does a joule measure?", ["energy"]),
    ("What does momentum equal?", ["mass", "velocity"]),
    ("What is revenue in terms of price and quantity?",
     ["price", "quantity"]),
]


def grade_ok(v, a, tol=2e-2):
    if v is None or a is None:
        return False
    try:
        v, a = float(v), float(a)
    except (TypeError, ValueError):
        return False
    if a == 0:
        return abs(v) < 1e-9
    return abs(v - a) / abs(a) <= tol


def gen_fact_recall(rng, n, prefix):
    out = []
    mats = sorted(MATERIALS)
    for i in range(n):
        m = mats[rng.randrange(len(mats))]
        d = MATERIALS[m]
        v = round(rng.uniform(0.2, 8.0), 2)
        stating = (i % 5) < 3          # 60/40 frozen split
        tpl = (FACT_STATING if stating else FACT_OMITTING)
        q = tpl[rng.randrange(len(tpl))].format(m=m, d=f"{d:g}",
                                                v=f"{v:g}")
        out.append({"id": f"{prefix}f{i:05d}", "q": q,
                    "answer": round(d * v, 6), "family": "fact",
                    "fact_mode": "stating" if stating else
                    "omitting", "material": m})
    return out


def gen_definitions(rng, n, prefix):
    out = []
    for i in range(n):
        qi = i % len(DEFINITIONS)
        q, a = DEFINITIONS[qi]
        item = {"id": f"{prefix}d{i:05d}", "q": q,
                "family": "definition", "def_key": qi}
        if isinstance(a, list):
            item["answer"] = None
            item["keywords"] = a
            item["expect"] = "text"
        else:
            item["answer"] = a
        out.append(item)
    rng.shuffle(out)
    return out


def main():
    if OUT.exists() and any(OUT.iterdir()):
        print("REFUSING: v1.1 data already exists (run-once).")
        sys.exit(2)
    OUT.mkdir(parents=True, exist_ok=True)
    from v11.genparse11 import gen_eval, gen_oof
    from v11.gensem11 import gen as gsem
    from v11.genadv11 import gen as gadv
    from reflex.engine import Engine
    t0 = time.time()

    # ---------------- G1: residual v2 (fixed-engine frontier)
    pool = gen_eval("xg1", G1_PARSE_SEED, G1_PARSE_N) + \
        gen_oof(G1_OOF_SEED, G1_OOF_N)
    eng = Engine(resolver=None, redundancy=True, use_breeder=True)
    residual, ok_n, wrong_n = [], 0, 0
    for i, it in enumerate(pool):
        r = eng.run_query(it["q"], f"g1_{i}")
        v = r.get("numeric_value")
        if grade_ok(v, it.get("answer")):
            ok_n += 1
            continue
        if v is not None:
            wrong_n += 1
            it = dict(it, fixed_engine_wrong=True)
        residual.append(it)
        if (i + 1) % 30000 == 0:
            print(f"  G1 filter {i+1}/{len(pool)}: residual "
                  f"{len(residual)}", flush=True)
    cov = ok_n / len(pool)
    print(f"G1 pool {len(pool)}: coverage {cov:.4f}, wrong "
          f"{wrong_n}, residual {len(residual)}")
    # AMENDMENT C: the W1b engine closed the generator universe; G1
    # becomes a residual-PROOF record. Any straggler is itemized in
    # full (no silent caps); the ablation runs only if a genuine
    # frontier reappears (it should not).
    from collections import Counter
    fam = Counter((x.get("quadrant"), x.get("template"))
                  for x in residual)
    splits = {"g1_residual_proof": [
        {"pool_n": len(pool), "coverage": cov, "wrong": wrong_n,
         "residual_n": len(residual),
         "families": {str(k): v for k, v in fam.most_common(20)},
         "stragglers": residual[:50]}]}

    # ---------------- G2: commercial 25k, varied topics
    rng2 = random.Random(G2_SEED)
    n_phys = int(G2_N * 0.82)
    n_fact = int(G2_N * 0.10)
    n_def = G2_N - n_phys - n_fact
    phys = gen_eval("xg2", G2_SEED, n_phys)
    for p in phys:
        p["family"] = "physmix"
    fact = gen_fact_recall(rng2, n_fact, "g2")
    defs = gen_definitions(rng2, n_def, "g2")
    commercial = phys + fact + defs
    rng2.shuffle(commercial)
    splits["g2_commercial"] = commercial

    # ---------------- G3: finals
    rng3 = random.Random(G3_SEED)
    n3_phys, n3_fact = 492, 60
    p3 = gen_eval("xg3", G3_SEED, n3_phys)
    for p in p3:
        p["family"] = "physmix"
    f3 = gen_fact_recall(rng3, n3_fact, "g3")
    d3 = gen_definitions(rng3, 600 - n3_phys - n3_fact, "g3")
    mixed = p3 + f3 + d3
    rng3.shuffle(mixed)
    splits["g3_sim_sealed"] = mixed
    splits["g3_sem_sealed"] = gsem("xb", SEM_SEED)
    splits["g3_adv_sealed"] = gadv("xb", ADV_SEED, 12)

    hashes = {"recipe": "expgen_v11.py",
              "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
              "g1_pool": {"n": len(pool),
                          "coverage": round(cov, 4),
                          "wrong": wrong_n,
                          "residual": len(residual),
                          "families": {str(k): v for k, v in
                                       fam.most_common(12)}}}
    for name, items in splits.items():
        p = OUT / f"{name}.json"
        p.write_text(json.dumps(items, indent=0), encoding="utf-8")
        hashes[name] = {"n": len(items), "sha256": hashlib.sha256(
            p.read_bytes()).hexdigest()}
        print(f"  {name}: n={len(items)} "
              f"sha={hashes[name]['sha256'][:12]}")
    (HERE / "results" / "expacq11" /
     "dataset_hashes_v11.json").write_text(
        json.dumps(hashes, indent=1), encoding="utf-8")
    print(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
