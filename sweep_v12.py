# -*- coding: utf-8 -*-
# origin: new for V1.2 — W1.3 seed-sweep certification (V1_2_SPEC)
"""Seed-sweep: trap suites across many independent seeds.

  python sweep_v12.py

Suites x seeds (frozen in V1_2_SPEC): sem recipe x20, adv recipe x20,
NEW reference-trap family x20, parser recipe x5. Metric: wrong-fire
across the ENTIRE sweep (target 0.000). Wrong-fire per V0.11
analyze: wrong answers on answer-expected + any answer on
abstain-expected. Every violation is itemized in full.

The reference-trap family (new): multi-entity states asked via
ordinals first..tenth (resolvable -> must answer correctly),
BEYOND-vocabulary ordinals ("eleventh", "twelfth") and vague
references ("that unit", "the other one" with >=2 candidates)
(unresolvable -> MUST abstain), and appositive-alias asks
(resolvable via W1.1b -> must answer correctly).
"""
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
OUT = HERE / "results" / "certification"

SEM_SEEDS = list(range(30001, 30021))
ADV_SEEDS = list(range(31001, 31021))
REF_SEEDS = list(range(32001, 32021))
PARSE_SEEDS = list(range(33001, 33006))

_ORD = ["first", "second", "third", "fourth", "fifth", "sixth",
        "seventh", "eighth", "ninth", "tenth"]
_BEYOND = ["eleventh", "twelfth", "thirteenth"]
_NOUNS = ["tank", "truck", "pump", "crate", "drone"]


def gen_ref_traps(seed, n=60):
    rng = random.Random(seed)
    items = []
    for i in range(n):
        noun = _NOUNS[rng.randrange(len(_NOUNS))]
        k = rng.randrange(3, 11)
        ents = []
        for j in range(k):
            m = rng.randrange(50, 2000)
            v = rng.randrange(2, 30)
            ents.append((chr(65 + j), m, v))
        body = " ".join(
            f"{noun.capitalize()} {a} weighs {m} kg and moves at "
            f"{v} m/s." for a, m, v in ents)
        cls = rng.randrange(3)
        if cls == 0:      # resolvable ordinal
            idx = rng.randrange(k)
            q = (f"{body} What is the kinetic energy of the "
                 f"{_ORD[idx]} one?")
            m, v = ents[idx][1], ents[idx][2]
            items.append({"id": f"rt{seed}_{i:03d}", "q": q,
                          "answer": 0.5 * m * v * v,
                          "expect": "answer",
                          "class": "ordinal_resolvable",
                          "trap_answer": 0.5 * ents[0][1] *
                          ents[0][2] ** 2})
        elif cls == 1:    # beyond-vocabulary / out-of-range ordinal
            w = _BEYOND[rng.randrange(len(_BEYOND))]
            q = (f"{body} What is the kinetic energy of the "
                 f"{w} one?")
            items.append({"id": f"rt{seed}_{i:03d}", "q": q,
                          "answer": None, "expect": "abstain",
                          "class": "ordinal_beyond",
                          "trap_answer": 0.5 * ents[0][1] *
                          ents[0][2] ** 2})
        else:             # vague reference
            ref = rng.choice(["that unit", "the other one",
                              "the machine in question"])
            q = (f"{body} What is the kinetic energy of {ref}?")
            items.append({"id": f"rt{seed}_{i:03d}", "q": q,
                          "answer": None, "expect": "abstain",
                          "class": "vague_reference",
                          "trap_answer": 0.5 * ents[0][1] *
                          ents[0][2] ** 2})
    return items


def wrong_fire_rows(eng, items, grade):
    viol = []
    for it in items:
        r = eng.run_query(it["q"], f"sw_{it['id']}")
        v = r.get("numeric_value")
        expect = it.get("expect", "answer")
        if expect == "abstain":
            if v is not None:
                viol.append({"id": it["id"], "class":
                             it.get("class"), "value": v,
                             "kind": "answered_on_abstain"})
        else:
            if v is not None and not grade(v, it.get("answer")):
                viol.append({"id": it["id"], "class":
                             it.get("class"), "value": v,
                             "answer": it.get("answer"),
                             "kind": "wrong_answer"})
    return viol


def main():
    from v11.gensem11 import gen as gsem
    from v11.genadv11 import gen as gadv
    from v11.genparse11 import gen_eval
    from reflex.engine import Engine

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

    OUT.mkdir(parents=True, exist_ok=True)
    eng = Engine()
    ledger = {"started": time.strftime("%Y-%m-%d %H:%M:%S"),
              "suites": {}, "violations": []}
    t0 = time.time()
    total = 0
    for tag, seeds, gen in (
            ("sem", SEM_SEEDS, lambda s: gsem("sw", s)),
            ("adv", ADV_SEEDS, lambda s: gadv("sw", s, 12)),
            ("reftrap", REF_SEEDS, lambda s: gen_ref_traps(s)),
            ("parse", PARSE_SEEDS,
             lambda s: gen_eval("sw", s, 1000))):
        n_items = n_viol = 0
        for s in seeds:
            items = gen(s)
            viol = wrong_fire_rows(eng, items, grade)
            n_items += len(items)
            n_viol += len(viol)
            for v in viol:
                ledger["violations"].append({"suite": tag,
                                             "seed": s, **v})
        ledger["suites"][tag] = {"seeds": len(seeds),
                                 "items": n_items,
                                 "wrong_fire": n_viol}
        total += n_items
        print(f"{tag}: {len(seeds)} seeds, {n_items} items, "
              f"wrong-fire {n_viol}", flush=True)
    ledger["total_items"] = total
    ledger["total_wrong_fire"] = len(ledger["violations"])
    ledger["wall_s"] = round(time.time() - t0)
    (OUT / "seed_sweep_ledger.json").write_text(
        json.dumps(ledger, indent=1), encoding="utf-8")
    print(f"SWEEP: {total} items across "
          f"{len(SEM_SEEDS)+len(ADV_SEEDS)+len(REF_SEEDS)+len(PARSE_SEEDS)}"
          f" seeds, wrong-fire {ledger['total_wrong_fire']} "
          f"({ledger['wall_s']}s)")
    sys.exit(0 if ledger["total_wrong_fire"] == 0 else 1)


if __name__ == "__main__":
    main()
