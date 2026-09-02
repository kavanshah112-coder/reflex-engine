# -*- coding: utf-8 -*-
# origin: new for V1.6 -- D-answers orchestration (SPEC 6, verifier phase)
"""Builds per-model answer batches from the ESCALATED share and, after
the bridge answers, grades them and runs the verifier battery.

  python tools/danswers16.py prep
      For each answering model: 200 DEV-phase items (from the M-all
      dev + ssci_dev escalations; verifier ADMISSION material) and
      400 SEALED-phase items (from the M-all seal + ssci_sealed
      escalations; the measurement). Frozen rules honoured:
        * items are the same for every model EXCEPT that no model
          receives a foreign item it authored itself;
        * distractor (narrative) escalations are included -- that is
          where LLM arithmetic errors live and the escalated share is
          exactly what an LLM would answer in production.
      Writes danswers_<model>_<phase>.json to the scratchpad dir
      (question text only -- no golds).

  python tools/danswers16.py score --model <m> --phase <dev|sealed>
      Reads answers_<model>_<phase>.json ({"id", "answer"} rows),
      grades against golds, runs reflex/verify16 on every row, and
      writes results/v16/dphase_<model>_<phase>.json with per-check
      fired/on-wrong/on-correct counts.
"""
import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))

SCRATCH = Path(r"C:\Users\admin\AppData\Local\Temp\claude"
               r"\C--Users-admin-Downloads"
               r"\1574de19-d241-4008-950c-857859d2f96d\scratchpad"
               r"\v16_danswers")
MODELS = ["haiku", "sonnet", "opus", "fable"]
DATA = HERE / "results" / "v16" / "data"
RES = HERE / "results" / "v16"


def _items(fname):
    return {i["id"]: i for i in json.loads(
        (DATA / fname).read_text(encoding="utf-8"))}


def _escalated(jsonl, items):
    out = []
    with open(RES / jsonl, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["status"] == "ESCALATED" and r["id"] in items:
                out.append(items[r["id"]])
    return out


def prep():
    rng = random.Random(1604)
    dev_pool = _escalated("M-all_dev.jsonl", _items("q100k_dev.json")) \
        + _escalated("M-all_ssci_dev.jsonl", _items("ssci_dev.json"))
    seal_pool = _escalated("M-all_seal.jsonl",
                           _items("q100k_seal.json")) \
        + _escalated("M-all_ssci_sealed.jsonl",
                     _items("ssci_sealed.json"))
    rng.shuffle(dev_pool)
    rng.shuffle(seal_pool)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for m in MODELS:
        for phase, pool, n in (("dev", dev_pool, 200),
                               ("sealed", seal_pool, 400)):
            picked, i = [], 0
            while len(picked) < n and i < len(pool):
                it = pool[i]
                i += 1
                if it.get("register") == "foreign" and \
                        it.get("author") == m:
                    continue          # never your own phrasing
                picked.append(it)
            (SCRATCH / ("danswers_%s_%s.json" % (m, phase))) \
                .write_text(json.dumps(
                    [{"id": it["id"], "question": it["text"]}
                     for it in picked], indent=0), encoding="utf-8")
            manifest["%s_%s" % (m, phase)] = len(picked)
    (SCRATCH / "manifest.json").write_text(json.dumps(manifest),
                                           encoding="utf-8")
    print(json.dumps({"dev_pool": len(dev_pool),
                      "seal_pool": len(seal_pool),
                      "batches": manifest}))


def _grade(item, answer_text):
    import v16_run as RUN
    import re
    gt = item.get("gold_type")
    s = str(answer_text).strip()
    if gt == "bool":
        low = s.lower()
        val = True if re.match(r"^(yes|true)\b", low) else \
            False if re.match(r"^(no|false)\b", low) else None
        return val is not None and val == bool(item["gold"])
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?(?:e-?\d+)?", s.replace(",", ""))
    if not m:
        return False
    try:
        v = float(m.group(0))
    except ValueError:
        return False
    if gt == "list":
        g = item["gold"]
        nums = [float(x) for x in re.findall(
            r"-?\d+(?:\.\d+)?", s.replace(",", ""))][:len(g)]
        return len(nums) == len(g) and all(
            abs(a - b) <= max(1e-4 * abs(b), 1e-4)
            for a, b in zip(sorted(nums), sorted(g)))
    try:
        g = float(item["gold"])
    except (TypeError, ValueError):
        return False
    return abs(v - g) <= max(2e-2 * abs(g), 1e-6)


def score(model, phase):
    from reflex import verify16
    batch = {r["id"]: r for r in json.loads(
        (SCRATCH / ("danswers_%s_%s.json" % (model, phase)))
        .read_text(encoding="utf-8"))}
    answers = json.loads(
        (SCRATCH / ("answers_%s_%s.json" % (model, phase)))
        .read_text(encoding="utf-8"))
    pool = {}
    for f in ("q100k_dev.json", "ssci_dev.json", "q100k_seal.json",
              "ssci_sealed.json"):
        pool.update(_items(f))
    per_check = defaultdict(lambda: Counter())
    n = Counter()
    rows = []
    for row in answers:
        iid = row["id"]
        if iid not in batch or iid not in pool:
            continue
        item = pool[iid]
        q = item["text"]
        ok = _grade(item, row["answer"])
        n["answered"] += 1
        n["correct" if ok else "wrong"] += 1
        v = verify16.verdict(q, str(row["answer"]))
        for flag in v["flags"]:
            per_check[flag]["fired"] += 1
            per_check[flag]["on_correct" if ok else "on_wrong"] += 1
        rows.append({"id": iid, "ok": ok, "flags": v["flags"],
                     "answer": str(row["answer"])[:60]})
    out = {"model": model, "phase": phase, "n": dict(n),
           "per_check": {k: dict(v) for k, v in
                         sorted(per_check.items())}}
    (RES / ("dphase_%s_%s.json" % (model, phase))).write_text(
        json.dumps({"summary": out, "rows": rows}, indent=1),
        encoding="utf-8")
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "score"])
    ap.add_argument("--model", choices=MODELS, default=None)
    ap.add_argument("--phase", choices=["dev", "sealed"],
                    default=None)
    a = ap.parse_args()
    if a.cmd == "prep":
        prep()
    else:
        score(a.model, a.phase)


if __name__ == "__main__":
    main()
