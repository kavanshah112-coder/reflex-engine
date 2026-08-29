# -*- coding: utf-8 -*-
# origin: new for V1.1 — bridge servicing helper (V1_1_SPEC §6)
"""Deferred-replay bridge servicing (no API keys):

  python service_bridge.py list  <model>   # pending -> batch files
  python service_bridge.py verify <model>  # resp sanity + remaining

Batches (<=40 reqs) are written to
results/bridge_v11/<model>/batches/batch_NNN.json; each is serviced
by ONE matching-model agent that reads every req file and writes
resp_<key>.json beside it. verify() rejects stubs (empty text, or
no JSON object where the miner prompt demands one).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRIDGE = HERE / "results" / "bridge_v11"
BATCH = 40


def pending(model):
    d = BRIDGE / model
    if not d.exists():
        return []
    return sorted(
        p for p in d.glob("req_*.json")
        if not (d / f"resp_{p.stem[4:]}.json").exists())


def do_list(model):
    reqs = pending(model)
    bdir = BRIDGE / model / "batches"
    bdir.mkdir(parents=True, exist_ok=True)
    for old in bdir.glob("batch_*.json"):
        old.unlink()
    for bi in range(0, len(reqs), BATCH):
        chunk = reqs[bi:bi + BATCH]
        (bdir / f"batch_{bi // BATCH:03d}.json").write_text(
            json.dumps([{"key": p.stem[4:], "req": str(p)}
                        for p in chunk], indent=1),
            encoding="utf-8")
    print(f"{model}: {len(reqs)} pending -> "
          f"{(len(reqs) + BATCH - 1) // BATCH} batch files in "
          f"{bdir}")


def do_verify(model):
    d = BRIDGE / model
    bad = 0
    for p in sorted(d.glob("resp_*.json")):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
            t = r.get("text") or ""
            assert t.strip()
            req = json.loads((d / f"req_{p.stem[5:]}.json")
                             .read_text(encoding="utf-8"))
            if "JSON only" in req.get("prompt", "") and \
                    "{" not in t:
                raise AssertionError("no JSON object")
        except Exception as e:
            bad += 1
            print("BAD", p.name, e)
            p.unlink()          # force re-service
    rem = len(pending(model))
    print(f"{model}: verify done, {bad} rejected, "
          f"{rem} still pending")
    return rem


if __name__ == "__main__":
    cmd, model = sys.argv[1], sys.argv[2]
    if cmd == "list":
        do_list(model)
    else:
        do_verify(model)
