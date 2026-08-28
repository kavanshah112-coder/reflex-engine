# -*- coding: utf-8 -*-
"""sem11 benchmark (spec Sections 5-6, 9): entity binding,
contradiction vs valid change (false-positive suite), quarantine.
Ground truth per item: expected answer OR expected abstention, plus
the trap answer a mis-binding would produce. dev seed 111 / sealed
seed 222; canonical hashes."""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NAMES = ["Car", "Tank", "Pump", "Truck", "Crate", "Drone", "Cart",
         "Sled", "Trolley", "Barge"]


def ke(m, v):
    return 0.5 * m * v * v


def _mk(rng, cls):
    """-> (text, answer_or_None, trap_answer_or_None, meta)"""
    if cls.startswith("bind"):
        n = {"bind2": 2, "bind3": 3, "bind5": 5, "bind10": 10}[cls]
        noun = rng.choice(NAMES)
        ents = []
        for i in range(n):
            m = rng.choice([800, 900, 1100, 1200, 1500]) + i
            v = rng.choice([5, 8, 10, 12, 15, 20]) + i
            ents.append((f"{noun} {chr(65 + i)}", m, v))
        target = rng.randrange(n)
        parts = [f"{nm} weighs {m} kg and moves at {v} m/s"
                 for nm, m, v in ents]
        text = ". ".join(parts) + ". "
        style = rng.choice(["name", "ordinal", "fastest"])
        tn, tm, tv = ents[target]
        if style == "name":
            ask = f"What is the kinetic energy of {tn.lower()}?"
        elif style == "ordinal":
            ordw = ["first", "second", "third", "fourth", "fifth",
                    "sixth", "seventh", "eighth", "ninth", "tenth"]
            ask = (f"What is the kinetic energy of the "
                   f"{ordw[target]} one?")
        else:
            target = max(range(n), key=lambda i: ents[i][2])
            tn, tm, tv = ents[target]
            ask = "What is the kinetic energy of the faster " \
                  f"{noun.lower()}?" if n == 2 else \
                  f"What is the kinetic energy of the fastest " \
                  f"{noun.lower()}?"
        others = [ke(m, v) for i, (nm, m, v) in enumerate(ents)
                  if i != target]
        return text + ask, ke(tm, tv), others[0] if others else None
    if cls == "alias":
        m1, v1 = rng.choice([(1200, 10), (900, 15), (1500, 8)])
        m2, v2 = rng.choice([(800, 20), (1100, 12)])
        text = (f"Car A — the red car — weighs {m1} kg and moves at "
                f"{v1} m/s. Car B weighs {m2} kg and moves at {v2} "
                f"m/s. What is the kinetic energy of the red car?")
        return text, ke(m1, v1), ke(m2, v2)
    if cls == "pronoun":
        m1, v1 = rng.choice([(600, 12), (1000, 9)])
        text = (f"The drone weighs {m1} kg. It cruises at {v1} m/s. "
                f"What is its kinetic energy?")
        return text, ke(m1, v1), None
    if cls == "conflict":
        m1, m2 = rng.choice([(20, 15), (50, 40), (12, 9)])
        h = rng.choice([5, 10, 20])
        text = (f"The crate weighs {m1} kg. The crate weighs {m2} "
                f"kg. It is lifted {h} m. What is its potential "
                f"energy?")
        return text, None, m1 * 9.8 * h     # correct = ABSTAIN
    if cls == "valid_change":
        m1, m2 = rng.choice([(20, 15), (50, 35), (80, 60)])
        text = (f"Initially the silo holds {m1} kg of grain; "
                f"finally it holds {m2} kg. How much mass was "
                f"lost?")
        return text, m1 - m2, None
    if cls == "cross_entity":
        m1, m2 = rng.choice([(20, 15), (60, 45)])
        h = rng.choice([4, 8])
        text = (f"Crate A weighs {m1} kg. Crate B weighs {m2} kg. "
                f"Crate A is lifted {h} m. What is the potential "
                f"energy of crate A?")
        return text, m1 * 9.8 * h, m2 * 9.8 * h
    if cls == "quarantine":
        m1, m2 = rng.choice([(20, 15), (44, 33)])
        mb = rng.choice([30, 70])
        v = rng.choice([6, 10])
        text = (f"Crate A weighs {m1} kg. Crate A weighs {m2} kg. "
                f"Crate B weighs {mb} kg and moves at {v} m/s. "
                f"What is the kinetic energy of crate B?")
        return text, ke(mb, v), None   # B independent of A conflict
    if cls == "quarantine_blocked":
        m1, m2 = rng.choice([(20, 15), (44, 33)])
        v = rng.choice([6, 10])
        text = (f"Crate A weighs {m1} kg. Crate A weighs {m2} kg. "
                f"Crate A moves at {v} m/s. What is the kinetic "
                f"energy of crate A?")
        return text, None, ke(m1, v)   # must ABSTAIN
    raise ValueError(cls)


CLASSES = (["bind2"] * 3 + ["bind3"] * 2 + ["bind5"] * 2 +
           ["bind10"] * 1 + ["alias"] * 2 + ["pronoun"] * 2 +
           ["conflict"] * 3 + ["valid_change"] * 3 +
           ["cross_entity"] * 2 + ["quarantine"] * 2 +
           ["quarantine_blocked"] * 2)
REPS = 5


def _sha(items):
    return hashlib.sha256(json.dumps(items, sort_keys=True,
                                     default=str).encode()).hexdigest()


def gen(split, seed):
    rng = random.Random(seed)
    items, seen = [], set()
    for rep in range(REPS):
        for cls in CLASSES:
            for _ in range(40):
                text, ans, trap = _mk(rng, cls)
                if text not in seen:
                    seen.add(text)
                    items.append({
                        "id": f"s11{split[0]}{len(items):04d}",
                        "q": text, "answer": ans,
                        "trap_answer": trap, "class": cls,
                        "expect": "answer" if ans is not None
                        else "abstain"})
                    break
    return items


def main():
    out = ROOT / "results/raw_v11"
    out.mkdir(parents=True, exist_ok=True)
    hp = out / "dataset_hashes_v11.json"
    hashes = json.loads(hp.read_text(encoding="utf-8")) \
        if hp.exists() else {}
    for split, seed in (("dev", 111), ("sealed", 222)):
        items = gen(split, seed)
        (out / f"sem11_{split}.json").write_text(
            json.dumps(items, indent=1), encoding="utf-8")
        hashes[f"sem11_{split}"] = {"sha256": _sha(items),
                                    "n": len(items)}
        print(split, len(items), hashes[f"sem11_{split}"]["sha256"][:12])
    hp.write_text(json.dumps(hashes, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
