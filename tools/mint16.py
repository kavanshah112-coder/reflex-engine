# -*- coding: utf-8 -*-
# origin: new for V1.6 -- Phase L orchestration (SPEC 5.2)
"""Prepares minting batches from ACQ residuals and runs returned
candidates through the acquire16 gauntlet.

  python tools/mint16.py prep --cap 1500
      reads results/v16/baseline_acq.jsonl + q100k_acq.json, takes
      ESCALATED in-domain items, groups by top taxonomy domain,
      samples up to --cap per model (same residual sample for every
      model -- the comparison is BETWEEN minters, so they must see
      the same material), writes per-model batch files to the
      scratchpad minting dir.

  python tools/mint16.py gauntlet --model haiku
      reads that model's returned candidate file, runs G1-G3 against
      the probation stream (escalated ACQ items with golds), writes
      results/v16/reflexlib_<model>.json + ledger + kills.

The bridge agents see ONLY the batch file: residual query texts and
the candidate schema. No golds, no engine modules, no parser source
(B9). Distractor residuals are EXCLUDED from what minters see -- no
reflex is ever offered narrative material (SPEC 6: the only claim on
distractors is escalation; minting on them could only manufacture a
SAFETY-2 hazard).
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
               r"\v16_mint")

MODELS = ["haiku", "sonnet", "opus", "fable"]


def load_residuals():
    items = {i["id"]: i for i in json.loads(
        (HERE / "results" / "v16" / "data" / "q100k_acq.json")
        .read_text(encoding="utf-8"))}
    resid = []
    with open(HERE / "results" / "v16" / "baseline_acq.jsonl",
              encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["status"] != "ESCALATED":
                continue
            it = items.get(r["id"])
            if it is None or it.get("distractor"):
                continue
            resid.append(it)
    return resid


def prep(cap):
    resid = load_residuals()
    rng = random.Random(1603)
    rng.shuffle(resid)
    sample = resid[:cap]
    by_dom = defaultdict(list)
    for it in sample:
        dom = (it["leaves"][0].split("/")[0] if it["leaves"]
               else "unknown")
        by_dom[dom].append(it)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    # one shared offer file (queries only), chunked by domain
    offers = []
    for dom in sorted(by_dom):
        for it in by_dom[dom]:
            offers.append({"domain": dom, "text": it["text"]})
    for m in MODELS:
        # 5 chunks per model to keep prompts tractable
        k = (len(offers) + 4) // 5
        for ci in range(5):
            chunk = offers[ci * k:(ci + 1) * k]
            (SCRATCH / ("offers_%s_%d.json" % (m, ci))).write_text(
                json.dumps(chunk, indent=0), encoding="utf-8")
    (SCRATCH / "sample_ids.json").write_text(
        json.dumps([it["id"] for it in sample]), encoding="utf-8")
    print(json.dumps({"residuals": len(resid), "offered": len(sample),
                      "domains": {d: len(v) for d, v in
                                  sorted(by_dom.items())},
                      "chunks_per_model": 5}))


def gauntlet(model):
    import v16_run as RUN
    from reflex import acquire16
    cands = []
    for ci in range(5):
        p = SCRATCH / ("candidates_%s_%d.json" % (model, ci))
        if p.exists():
            try:
                cands.extend(json.loads(p.read_text(encoding="utf-8")))
            except json.JSONDecodeError as e:
                print("chunk %d unparseable: %s" % (ci, e))
    items = {i["id"]: i for i in json.loads(
        (HERE / "results" / "v16" / "data" / "q100k_acq.json")
        .read_text(encoding="utf-8"))}
    sample_ids = json.loads((SCRATCH / "sample_ids.json")
                            .read_text(encoding="utf-8"))
    probation = [(items[i], items[i]["text"]) for i in sample_ids
                 if i in items]

    def grade_fn(item, value):
        return RUN.grade(item, value)

    admitted, ledger, kills = acquire16.gauntlet(cands, probation,
                                                 grade_fn)
    ledger["model"] = model
    ledger["offered"] = len(probation)
    out = HERE / "results" / "v16"
    (out / ("reflexlib_%s.json" % model)).write_text(
        json.dumps(admitted, indent=1), encoding="utf-8")
    (out / ("mint_ledger_%s.json" % model)).write_text(
        json.dumps({"ledger": ledger, "kills": kills}, indent=1),
        encoding="utf-8")
    print(json.dumps(ledger, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "gauntlet"])
    ap.add_argument("--cap", type=int, default=1500)
    ap.add_argument("--model", default=None, choices=MODELS + [None])
    a = ap.parse_args()
    if a.cmd == "prep":
        prep(a.cap)
    else:
        assert a.model
        gauntlet(a.model)


if __name__ == "__main__":
    main()
