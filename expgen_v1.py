# -*- coding: utf-8 -*-
# origin: new for V1.0 — EXP-ACQ pre-registered generator (V1_PLAN §1)
"""EXP-ACQ dataset generation. COMMITTED BEFORE ANY ITEM EXISTS; the
commit hash is the pre-registration of this recipe. Run exactly once;
outputs are hash-recorded and never regenerated after evaluation.

Recipe (frozen):
 1. Candidate pool = v0.11-recipe parser generation with FRESH seeds:
    gen_eval("xa", seed 5555, n 18000) + gen_oof(seed 5556, n 2500).
 2. Escalated-residual filter: run the FROZEN v1.0-parity engine
    (pack path, breeder on, resolver OFF — stream construction must
    not depend on an LLM) over the pool; keep items the engine does
    NOT answer correctly-deterministically (abstentions AND wrong
    answers both stay: the stream is 'what would reach the LLM').
    Wrong-answer counts are reported, not hidden (no silent caps).
 3. Deterministic shuffle (seed 5557), then disjoint splits:
      validation 1,000  (frozen BEFORE traffic; checkpoint probes)
      traffic    5,000  (replayed identically to every arm)
      sealed parser final 500 (evaluated once, at the end)
    Pool must cover 6,500; anything less is a loud failure.
 4. Integrity finals (fresh seeds, v0.11 recipes unchanged):
      sem final  = gensem11.gen("xa", 7222)         (~76)
      adv final  = genadv11.gen("xa", 7666, per=12) (~122)
 5. sha256 of every emitted file -> results/expacq/dataset_hashes.json

  python expgen_v1.py
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

OUT = HERE / "results" / "expacq" / "data"

POOL_PARSE_SEED, POOL_PARSE_N = 5555, 18000
POOL_OOF_SEED, POOL_OOF_N = 5556, 2500
SHUFFLE_SEED = 5557
N_VAL, N_TRAFFIC, N_SEALED = 1000, 5000, 500
SEM_SEED, ADV_SEED, ADV_PER = 7222, 7666, 12


def grade(v, a, tol=2e-2):
    if v is None or a is None:
        return False
    try:
        v, a = float(v), float(a)
    except (TypeError, ValueError):
        return False
    if a == 0:
        return abs(v) < 1e-9
    return abs(v - a) / abs(a) <= tol


def main():
    if OUT.exists() and any(OUT.iterdir()):
        print("REFUSING: expacq data already exists; this recipe "
              "runs exactly once.")
        sys.exit(2)
    OUT.mkdir(parents=True, exist_ok=True)
    from v11.genparse11 import gen_eval, gen_oof
    from v11.gensem11 import gen as gsem
    from v11.genadv11 import gen as gadv
    from reflex.engine import Engine

    t0 = time.time()
    pool = gen_eval("xa", POOL_PARSE_SEED, POOL_PARSE_N) + \
        gen_oof(POOL_OOF_SEED, POOL_OOF_N)
    print(f"pool generated: {len(pool)}")

    eng = Engine(resolver=None, redundancy=True, use_breeder=True)
    residual, answered_ok, answered_wrong = [], 0, 0
    for i, it in enumerate(pool):
        r = eng.run_query(it["q"], f"xg_{i}")
        v = r.get("numeric_value")
        if v is not None and grade(v, it.get("answer")):
            answered_ok += 1
            continue
        if v is not None:
            answered_wrong += 1
            it = dict(it, frozen_engine_wrong=True)
        residual.append(it)
        if (i + 1) % 4000 == 0:
            print(f"  filtered {i+1}/{len(pool)}: "
                  f"residual {len(residual)}", flush=True)
    cov = answered_ok / len(pool)
    print(f"frozen-engine pool coverage: {cov:.3f}  "
          f"(answered_ok {answered_ok}, wrong {answered_wrong}, "
          f"residual {len(residual)})")
    need = N_VAL + N_TRAFFIC + N_SEALED
    assert len(residual) >= need, \
        f"pool too small: residual {len(residual)} < {need}"

    rng = random.Random(SHUFFLE_SEED)
    rng.shuffle(residual)
    splits = {
        "expacq_val": residual[:N_VAL],
        "expacq_traffic": residual[N_VAL:N_VAL + N_TRAFFIC],
        "expacq_parse_sealed":
            residual[N_VAL + N_TRAFFIC:need],
        "expacq_sem_sealed": gsem("xa", SEM_SEED),
        "expacq_adv_sealed": gadv("xa", ADV_SEED, ADV_PER),
    }
    hashes = {"recipe": "expgen_v1.py", "generated": time.strftime(
        "%Y-%m-%d %H:%M:%S"),
        "pool": {"n": len(pool), "coverage": round(cov, 4),
                 "answered_wrong": answered_wrong,
                 "residual": len(residual)}}
    for name, items in splits.items():
        p = OUT / f"{name}.json"
        p.write_text(json.dumps(items, indent=0),
                     encoding="utf-8")
        hashes[name] = {
            "n": len(items),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        print(f"  {name}: n={len(items)} "
              f"sha={hashes[name]['sha256'][:12]}")
    (HERE / "results" / "expacq" /
     "dataset_hashes.json").write_text(
        json.dumps(hashes, indent=1), encoding="utf-8")
    print(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
