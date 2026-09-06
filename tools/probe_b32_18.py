# -*- coding: utf-8 -*-
# origin: new for V1.8 -- PROBE-B32 and the haiku-13 corpus (SPEC 4.5)
"""Rebuilds the version's positive controls from the committed V1.7
record only:

  PROBE-B32   every wrong row of R-<model>_{acq,dev,seal,replay}
              _wrong.json (8,842 expected), joined by id to the
              full Q-1M item and by template name to stack_<model>
              .json -> results/v18/probe_b32.json
  haiku-13    the certified-WRONG sealed S-PLAN serves of haiku
              (plans_haiku_sealed.json rows with gate true and
              correct false) with their plans from
              planlib_haiku_sealed.json -> results/v18/probe_haiku13.json

  python tools/probe_b32_18.py
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
V17 = HERE / "results" / "v17"
DATA = V17 / "data"
OUT = HERE / "results" / "v18"
MODELS = ["haiku", "sonnet", "opus", "fable"]
SPLITS = ["acq", "dev", "seal", "replay"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    want = {}                      # split -> {id -> [(model, row)]}
    for m in MODELS:
        for s in SPLITS:
            p = V17 / ("R-%s_%s_wrong.json" % (m, s))
            rows = json.loads(p.read_text(encoding="utf-8"))["wrong"]
            for r in rows:
                want.setdefault(s, {}).setdefault(r["id"], []).append(
                    (m, r))
    stacks = {}
    for m in MODELS:
        stacks[m] = {c["name"]: c for c in json.loads(
            (V17 / ("stack_%s.json" % m)).read_text(encoding="utf-8"))}
    probe, missing_tpl = [], 0
    for s in SPLITS:
        ids = want.get(s, {})
        with open(DATA / ("q1m_%s.jsonl" % s), encoding="utf-8") as f:
            for line in f:
                it = json.loads(line)
                if it["id"] not in ids:
                    continue
                for m, r in ids[it["id"]]:
                    name = (r["path"] or "").split(":")[-1]
                    tpl = stacks[m].get(name)
                    if tpl is None:
                        missing_tpl += 1
                    probe.append({
                        "model": m, "split": s, "id": it["id"],
                        "text": it["text"], "gold": it["gold"],
                        "gold_type": it["gold_type"], "k": it["k"],
                        "wrong_value": r["value"], "path": r["path"],
                        "template": ({"name": name,
                                      "pattern": tpl["pattern"],
                                      "plan": tpl["plan"]}
                                     if tpl else None)})
    probe.sort(key=lambda r: (r["model"], r["split"], r["id"]))
    p = OUT / "probe_b32.json"
    p.write_text(json.dumps({"n": len(probe),
                             "templates_missing": missing_tpl,
                             "rows": probe}, indent=1),
                 encoding="utf-8")
    # haiku-13
    scored = json.loads((V17 / "plans_haiku_sealed.json")
                        .read_text(encoding="utf-8"))
    wrong_ids = {r["id"] for r in scored["rows"]
                 if r.get("gate") and r.get("correct") is False}
    plans = {a["id"]: a for a in json.loads(
        (V17 / "planlib_haiku_sealed.json").read_text(encoding="utf-8"))}
    h13 = []
    with open(DATA / "q1m_seal.jsonl", encoding="utf-8") as f:
        for line in f:
            it = json.loads(line)
            if it["id"] in wrong_ids:
                h13.append({"id": it["id"], "text": it["text"],
                            "gold": it["gold"], "k": it["k"],
                            "gold_type": it["gold_type"],
                            "plan": plans[it["id"]]["plan"]})
    h13.sort(key=lambda r: r["id"])
    q = OUT / "probe_haiku13.json"
    q.write_text(json.dumps({"n": len(h13), "rows": h13}, indent=1),
                 encoding="utf-8")
    hashes = {"probe_b32.json": hashlib.sha256(p.read_bytes())
              .hexdigest(),
              "probe_haiku13.json": hashlib.sha256(q.read_bytes())
              .hexdigest()}
    (OUT / "probe_hashes.json").write_text(json.dumps(hashes, indent=1),
                                           encoding="utf-8")
    print(json.dumps({"probe_b32": len(probe),
                      "templates_missing": missing_tpl,
                      "haiku13": len(h13), "hashes": hashes},
                     indent=1))


if __name__ == "__main__":
    main()
