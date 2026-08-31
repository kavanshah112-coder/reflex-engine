# -*- coding: utf-8 -*-
# origin: new for V1.3 — pre-registered generator (V1_3_SPEC §11)
"""V1.3 dataset generation. COMMITTED BEFORE RUNNING; run once.

Draws fresh splits from the UNUSED remainder of the frozen V1.2
corpora, asserting disjointness from every id V1.2 consumed.

Splits (sizes frozen in V1_3_SPEC §11):
  theory_sealed  100  (SciQ; conceptual, expect abstain or TEXT)
  units_sealed   150  (unit-bearing GSM8K/ASDiv — the design domain)
  full_sealed    300  (GSM8K/ASDiv, unfiltered)
  arm_sample     300  (paired parse-model comparison; NOT sealed)
  traffic_pool  ~1180 (mixed; the recurrence + acquisition stream)

Traffic modes (both, per decision v):
  T-repeat  3,000 draws WITH replacement from traffic_pool
  T-unique  traffic_pool itself, no replacement

GSM8K items keep their reference solution text (the inline
<<a op b=c>> calculator annotations) because W0 reads operation
structure from it at zero model cost. Sealed items are never touched
by W0 — recurrence is measured on the traffic pool only.
"""
import hashlib
import json
import random
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
COR = HERE / "corpora"
V12 = HERE / "results" / "real" / "data"
OUT = HERE / "results" / "v13" / "data"

SEED_SHUFFLE, SEED_STREAM = 51001, 51002
N_THEORY, N_UNITS, N_FULL, N_ARM = 100, 150, 300, 300
N_TRAFFIC_POOL, N_REPEAT = 1180, 3000

UNIT_TOKENS = re.compile(
    r"\b(kg|kilograms?|grams?|tonnes?|m/s|km/h|kph|metres?|meters?|"
    r"km|cm|litres?|liters?|ml|watts?|kw|volts?|amps?|ohms?|joules?|"
    r"kwh|hours?|minutes?|seconds?|dollars?|cents?|miles?|pounds?|"
    r"gallons?|inches|feet|yards?)\b|\$|°c", re.I)


def v12_consumed():
    ids = set()
    for p in V12.glob("*.json"):
        try:
            for it in json.loads(p.read_text(encoding="utf-8")):
                if isinstance(it, dict) and it.get("id"):
                    ids.add(it["id"])
        except Exception:
            continue
    return ids


def load_gsm8k():
    out = []
    for i, line in enumerate((COR / "gsm8k_test.jsonl")
                             .read_text(encoding="utf-8").splitlines()):
        d = json.loads(line)
        m = re.search(r"####\s*([-\d,\.]+)", d["answer"])
        if not m:
            continue
        try:
            ans = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        out.append({"id": f"gsm{i:04d}", "q": d["question"].strip(),
                    "answer": ans, "source": "gsm8k",
                    "solution": d["answer"]})
    return out


def load_asdiv():
    root = ET.parse(COR / "asdiv.xml").getroot()
    out = []
    for i, p in enumerate(root.iter("Problem")):
        body = (p.findtext("Body") or "").strip()
        q = (p.findtext("Question") or "").strip()
        a = (p.findtext("Answer") or "").strip()
        f = (p.findtext("Formula") or "").strip()
        m = re.match(r"([-\d\.]+)", a.replace(",", ""))
        if not (body and q and m):
            continue
        try:
            ans = float(m.group(1))
        except ValueError:
            continue
        out.append({"id": f"asdiv{i:04d}", "q": f"{body} {q}",
                    "answer": ans, "source": "asdiv",
                    "solution": f})
    return out


def load_sciq():
    with zipfile.ZipFile(COR / "sciq.zip") as z:
        name = [n for n in z.namelist() if n.endswith("test.json")][0]
        data = json.loads(z.read(name).decode("utf-8"))
    out = []
    for i, d in enumerate(data):
        q = (d.get("question") or "").strip()
        a = (d.get("correct_answer") or "").strip()
        if not q or not a or len(a) < 2:
            continue
        out.append({"id": f"sciq{i:04d}", "q": q, "answer": None,
                    "expect": "text", "keywords": [a],
                    "source": "sciq", "family": "theory"})
    return out


def main():
    if OUT.exists() and any(OUT.iterdir()):
        print("REFUSING: v13 data exists (run-once).")
        sys.exit(2)
    OUT.mkdir(parents=True, exist_ok=True)
    spent = v12_consumed()
    print(f"V1.2 consumed {len(spent)} ids (excluded)")

    gsm = [x for x in load_gsm8k() if x["id"] not in spent]
    asd = [x for x in load_asdiv() if x["id"] not in spent]
    sci = [x for x in load_sciq() if x["id"] not in spent]
    print(f"available: gsm8k {len(gsm)}, asdiv {len(asd)}, "
          f"sciq {len(sci)}")

    rng = random.Random(SEED_SHUFFLE)
    rng.shuffle(gsm)
    rng.shuffle(asd)
    rng.shuffle(sci)

    numeric = gsm + asd
    rng.shuffle(numeric)
    units_pool = [x for x in numeric if UNIT_TOKENS.search(x["q"])]
    units_ids = {x["id"] for x in units_pool}

    splits = {}
    splits["v13_theory_sealed"] = sci[:N_THEORY]
    rest_sci = sci[N_THEORY:]

    splits["v13_units_sealed"] = units_pool[:N_UNITS]
    taken = {x["id"] for x in splits["v13_units_sealed"]}

    rest_num = [x for x in numeric if x["id"] not in taken]
    splits["v13_full_sealed"] = rest_num[:N_FULL]
    taken |= {x["id"] for x in splits["v13_full_sealed"]}

    rest_num = [x for x in numeric if x["id"] not in taken]
    splits["v13_arm_sample"] = rest_num[:N_ARM]
    taken |= {x["id"] for x in splits["v13_arm_sample"]}

    rest_num = [x for x in numeric if x["id"] not in taken]
    n_theory_traffic = int(N_TRAFFIC_POOL * 0.2)
    pool = rest_num[:N_TRAFFIC_POOL - n_theory_traffic] + \
        rest_sci[:n_theory_traffic]
    rng.shuffle(pool)
    splits["v13_traffic_pool"] = pool

    # both traffic modes over the SAME pool
    rng2 = random.Random(SEED_STREAM)
    splits["v13_traffic_repeat"] = [
        dict(pool[rng2.randrange(len(pool))], sid=f"tr{i:05d}")
        for i in range(N_REPEAT)]
    uniq = list(pool)
    rng2.shuffle(uniq)
    splits["v13_traffic_unique"] = [
        dict(x, sid=f"tu{i:05d}") for i, x in enumerate(uniq)]

    # disjointness assertions
    sealed_ids = set()
    for k in ("v13_theory_sealed", "v13_units_sealed",
              "v13_full_sealed"):
        ids = {x["id"] for x in splits[k]}
        assert not (ids & sealed_ids), f"sealed overlap in {k}"
        sealed_ids |= ids
    arm_ids = {x["id"] for x in splits["v13_arm_sample"]}
    pool_ids = {x["id"] for x in splits["v13_traffic_pool"]}
    assert not (sealed_ids & arm_ids), "sealed/arm overlap"
    assert not (sealed_ids & pool_ids), "sealed/traffic overlap"
    assert not (arm_ids & pool_ids), "arm/traffic overlap"
    assert not (sealed_ids & spent), "V1.2 reuse in sealed"
    assert not (pool_ids & spent), "V1.2 reuse in traffic"
    print("disjointness: sealed / arm / traffic / V1.2 all clean")

    hashes = {"recipe": "expgen_v13.py",
              "v12_consumed_ids": len(spent),
              "seeds": {"shuffle": SEED_SHUFFLE,
                        "stream": SEED_STREAM}}
    for name, items in splits.items():
        p = OUT / f"{name}.json"
        p.write_text(json.dumps(items, indent=0), encoding="utf-8")
        hashes[name] = {"n": len(items),
                        "sha256": hashlib.sha256(
                            p.read_bytes()).hexdigest()}
        print(f"  {name}: n={len(items)} "
              f"sha={hashes[name]['sha256'][:12]}")
    (HERE / "results" / "v13" / "dataset_hashes_v13.json").write_text(
        json.dumps(hashes, indent=1), encoding="utf-8")
    print("frozen.")


if __name__ == "__main__":
    main()
