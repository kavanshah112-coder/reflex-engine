# -*- coding: utf-8 -*-
# origin: new for V1.6 -- fold bridge-authored phrasings into the data
"""Destinations are fixed by sheet index, independent of author:

    fs16_00000 .. fs16_02999   -> Q-100K foreign slots (3,000)
    fs16_03000 .. fs16_03399   -> S-SCI-dev   (400)
    fs16_03400 .. fs16_05399   -> S-SCI-sealed (2,000)

A Q-100K slot item is REPLACED whole: the authored text plus the fact
sheet's gold/witness/labels (register 'foreign', author recorded).
S-SCI files are built fresh. After the merge the final pre-seal
hashes are recorded over raw bytes; the seal files are then run once.

Refuses to run if any sheet lacks an authored text — a partial merge
would silently shrink the foreign register.

  python tools/merge_foreign16.py [--authored-dir <dir>]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "results" / "v16" / "data"
DEFAULT_AUTHOR_DIR = Path(
    r"C:\Users\admin\AppData\Local\Temp\claude"
    r"\C--Users-admin-Downloads"
    r"\1574de19-d241-4008-950c-857859d2f96d\scratchpad\v16_author")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--authored-dir", default=str(DEFAULT_AUTHOR_DIR))
    a = ap.parse_args()
    adir = Path(a.authored_dir)

    sheets = {s["sheet_id"]: s for s in json.loads(
        (DATA / "factsheets.json").read_text(encoding="utf-8"))}
    assign = json.loads((adir / "assignment.json")
                        .read_text(encoding="utf-8"))
    texts = {}
    for p in sorted(adir.glob("authored_*.json")):
        for row in json.loads(p.read_text(encoding="utf-8")):
            texts[row["sheet_id"]] = row["text"].strip()

    missing = sorted(set(sheets) - set(texts))
    if missing:
        print("REFUSING: %d sheets lack authored text (first: %s)"
              % (len(missing), missing[:5]))
        sys.exit(1)

    def foreign_item(sid, iid):
        s = sheets[sid]
        return {"id": iid, "text": texts[sid], "gold": s["gold"],
                "gold_type": s["gold_type"], "witness": s["witness"],
                "leaves": s["leaves"], "depth": s["depth"],
                "nonmono": bool(s.get("nonmono")),
                "register": "foreign", "author": assign[sid],
                "sheet_id": sid, "distractor": False}

    ordered = sorted(sheets)                     # fs16_00000 ...
    slot_sheets = ordered[:3000]
    dev_sheets = ordered[3000:3400]
    seal_sheets = ordered[3400:5400]

    # --- replace Q-100K foreign slots (in file order, per split) ---
    si = 0
    replaced = Counter()
    for split in ("acq", "dev", "seal"):
        p = DATA / ("q100k_%s.json" % split)
        items = json.loads(p.read_text(encoding="utf-8"))
        for i, it in enumerate(items):
            if it.get("register") == "foreign_slot":
                items[i] = foreign_item(slot_sheets[si], it["id"])
                si += 1
                replaced[split] += 1
        p.write_text(json.dumps(items, indent=0), encoding="utf-8")
    assert si == 3000, "slot count mismatch: %d" % si

    # --- S-SCI sets -----------------------------------------------
    (DATA / "ssci_dev.json").write_text(json.dumps(
        [foreign_item(s, "ssci_dev_%04d" % i)
         for i, s in enumerate(dev_sheets)], indent=0),
        encoding="utf-8")
    (DATA / "ssci_sealed.json").write_text(json.dumps(
        [foreign_item(s, "ssci_seal_%04d" % i)
         for i, s in enumerate(seal_sheets)], indent=0),
        encoding="utf-8")

    authors = Counter(assign[s] for s in ordered)
    print(json.dumps({"replaced": dict(replaced),
                      "ssci_dev": len(dev_sheets),
                      "ssci_sealed": len(seal_sheets),
                      "authors": dict(authors)}))


if __name__ == "__main__":
    main()
