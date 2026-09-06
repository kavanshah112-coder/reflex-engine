# -*- coding: utf-8 -*-
# origin: new for V1.8 -- DEV-L, the sealed-shaped dev set (SPEC 5, 12.1)
"""400k programmatic chain items from V1.7's FROZEN generator with a
new seed, plus the Q-1M ACQ/DEV distractor items, hash-checked
disjoint from SEAL and REPLAY by text.

  python tools/build_devl18.py [--n 400000] [--seed 1800]

Writes results/v18/data/devl.jsonl, devl_manifest.json and
devl_hashes.json (raw-byte SHA-256). build_q1m is imported, never
edited: gen_item and K_MIX are V1.7's byte-for-byte.
"""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tools"))
import build_q1m as BQ  # noqa: E402

V17 = HERE / "results" / "v17" / "data"
OUT = HERE / "results" / "v18" / "data"


def _texts(split):
    s = set()
    with open(V17 / ("q1m_%s.jsonl" % split), encoding="utf-8") as f:
        for line in f:
            s.add(json.loads(line)["text"])
    return s


def _distractors():
    out = []
    for split in ("acq", "dev"):
        with open(V17 / ("q1m_%s.jsonl" % split),
                  encoding="utf-8") as f:
            for line in f:
                it = json.loads(line)
                if it.get("distractor"):
                    out.append(it)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400000)
    ap.add_argument("--seed", type=int, default=1800)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    sealed_texts = _texts("seal") | _texts("replay")
    print("sealed+replay texts:", len(sealed_texts), flush=True)
    distr = _distractors()
    n_dist = len(distr)
    n_prog = a.n - n_dist
    rng = random.Random(a.seed)
    quota = {k: round(n_prog * f) for k, f in BQ.K_MIX}
    quota[3] += n_prog - sum(quota.values())
    made = {k: 0 for k in quota}
    items, rejects, collisions, idx = [], 0, 0, 0
    seen = set()
    internal_dups = 0
    while sum(made.values()) < n_prog:
        k = next(kk for kk, _f in BQ.K_MIX if made[kk] < quota[kk])
        it = BQ.gen_item(rng, k)
        if it is None:
            rejects += 1
            if rejects > n_prog:
                raise RuntimeError("generator reject rate too high")
            continue
        if it["text"] in sealed_texts:
            collisions += 1
            continue
        if it["text"] in seen:
            internal_dups += 1
        seen.add(it["text"])
        it["id"] = "q18_%07d" % idx
        idx += 1
        items.append(it)
        made[k] += 1
        if idx % 50000 == 0:
            print("generated", idx, "collisions", collisions,
                  flush=True)
    items.extend(distr)
    rng.shuffle(items)
    path = OUT / "devl.jsonl"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    nm = sum(1 for i in items if i.get("nonmono"))
    md = sum(1 for i in items if i.get("multidomain"))
    manifest = {"seed": a.seed, "n": len(items), "programmatic": n_prog,
                "distractors": n_dist,
                "distractor_source": "Q-1M ACQ+DEV distractor items "
                                     "(disjoint from SEAL/REPLAY)",
                "foreign_slots": 0,
                "sealed_text_collisions_rejected": collisions,
                "internal_duplicate_texts": internal_dups,
                "rejects": rejects, "k_quota": quota,
                "nonmono_share": round(nm / max(1, n_prog), 4),
                "multidomain_share": round(md / max(1, n_prog), 4),
                "sha256_devl_jsonl": h}
    (OUT / "devl_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    (OUT / "devl_hashes.json").write_text(
        json.dumps({"devl.jsonl": h}, indent=1), encoding="utf-8")
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
