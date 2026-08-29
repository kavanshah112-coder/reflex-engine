# -*- coding: utf-8 -*-
# origin: new for V1.2 — W2.1 real-language corpus builder
"""Builds the frozen real-language tracks from the downloaded
corpora (run once; hashes recorded; licenses noted).

Sources (downloaded 2026-08-29, raw files hashed):
  GSM8K test (MIT license) — human-written grade-school problems.
  ASDiv (CC BY-NC 4.0 — research use) — diverse arithmetic/word.
  SciQ (CC BY-NC 3.0 — research use) — crowd-written science exam
  questions with answer keys (the THEORY track).

Tracks (V1_2_SPEC frozen): FULL n=1000 sealed 300; UNITS n>=300
sealed 120; THEORY n=300 sealed 100. Real-language TRAFFIC stream =
3,000 draws with replacement (seed 42001) from the non-sealed pools
at FULL:UNITS:THEORY = 60:20:20 — repetition models real recurring
usage and gives the TEXT/MEMORY quorums a fair chance.
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
OUT = HERE / "results" / "real" / "data"

UNIT_TOKENS = re.compile(
    r"\b(kg|kilograms?|grams?|tonnes?|m/s|km/h|kph|metres?|meters?|"
    r"km|cm|litres?|liters?|ml|watts?|kw|volts?|amps?|ohms?|"
    r"joules?|kwh|hours?|minutes?|seconds?|dollars?)\b|\$|°c",
    re.I)


def load_gsm8k():
    out = []
    for i, line in enumerate((COR / "gsm8k_test.jsonl")
                             .read_text(encoding="utf-8")
                             .splitlines()):
        d = json.loads(line)
        m = re.search(r"####\s*([-\d,\.]+)", d["answer"])
        if not m:
            continue
        try:
            ans = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        out.append({"id": f"gsm{i:04d}", "q": d["question"].strip(),
                    "answer": ans, "source": "gsm8k"})
    return out


def load_asdiv():
    root = ET.parse(COR / "asdiv.xml").getroot()
    out = []
    for i, p in enumerate(root.iter("Problem")):
        body = (p.findtext("Body") or "").strip()
        q = (p.findtext("Question") or "").strip()
        a = (p.findtext("Answer") or "").strip()
        m = re.match(r"([-\d\.]+)", a.replace(",", ""))
        if not (body and q and m):
            continue
        try:
            ans = float(m.group(1))
        except ValueError:
            continue
        out.append({"id": f"asdiv{i:04d}", "q": f"{body} {q}",
                    "answer": ans, "source": "asdiv"})
    return out


def load_sciq():
    with zipfile.ZipFile(COR / "sciq.zip") as z:
        name = [n for n in z.namelist()
                if n.endswith("test.json")][0]
        data = json.loads(z.read(name).decode("utf-8"))
    out = []
    for i, d in enumerate(data):
        q = (d.get("question") or "").strip()
        a = (d.get("correct_answer") or "").strip()
        if not q or not a or len(a) < 2:
            continue
        out.append({"id": f"sciq{i:04d}", "q": q,
                    "answer": None, "expect": "text",
                    "keywords": [a], "source": "sciq",
                    "family": "theory"})
    return out


def main():
    if OUT.exists() and any(OUT.iterdir()):
        print("REFUSING: real-language data exists (run-once)")
        sys.exit(2)
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42000)
    gsm = load_gsm8k()
    asdiv = load_asdiv()
    sciq = load_sciq()
    print(f"loaded: gsm8k {len(gsm)}, asdiv {len(asdiv)}, "
          f"sciq {len(sciq)}")
    rng.shuffle(gsm)
    rng.shuffle(asdiv)
    rng.shuffle(sciq)
    full = (gsm[:600] + asdiv[:400])
    rng.shuffle(full)
    units_pool = [x for x in gsm + asdiv
                  if UNIT_TOKENS.search(x["q"])]
    rng.shuffle(units_pool)
    units = units_pool[:max(300, min(400, len(units_pool)))]
    theory = sciq[:300]
    splits = {
        "real_full_sealed": full[:300],
        "real_full_traffic_pool": full[300:],
        "real_units_sealed": units[:120],
        "real_units_traffic_pool": units[120:],
        "real_theory_sealed": theory[:100],
        "real_theory_traffic_pool": theory[100:],
    }
    # the traffic stream: draws with replacement (recurring usage)
    rng2 = random.Random(42001)
    pools = (splits["real_full_traffic_pool"],
             splits["real_units_traffic_pool"],
             splits["real_theory_traffic_pool"])
    weights = (0.6, 0.2, 0.2)
    stream = []
    for i in range(3000):
        x = rng2.random()
        pool = pools[0] if x < weights[0] else \
            pools[1] if x < weights[0] + weights[1] else pools[2]
        it = pool[rng2.randrange(len(pool))]
        stream.append(dict(it, sid=f"rt{i:05d}"))
    splits["real_traffic_stream"] = stream

    hashes = {"raw_files": {f.name: hashlib.sha256(
        f.read_bytes()).hexdigest() for f in COR.iterdir()},
        "licenses": {"gsm8k": "MIT",
                     "asdiv": "CC BY-NC 4.0 (research use)",
                     "sciq": "CC BY-NC 3.0 (research use)"}}
    for name, items in splits.items():
        p = OUT / f"{name}.json"
        p.write_text(json.dumps(items, indent=0), encoding="utf-8")
        hashes[name] = {"n": len(items),
                        "sha256": hashlib.sha256(
                            p.read_bytes()).hexdigest()}
        print(f"  {name}: n={len(items)}")
    (HERE / "results" / "real" / "corpus_hashes.json").write_text(
        json.dumps(hashes, indent=1), encoding="utf-8")
    print("frozen.")


if __name__ == "__main__":
    main()
