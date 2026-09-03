# -*- coding: utf-8 -*-
# origin: new for V1.7 -- fold authored chain phrasings into Q-1M
"""Replaces every foreign_slot item in the four Q-1M splits with a
fact-sheet item carrying the bridge-authored text (register 'foreign',
author recorded). Slot order maps to sheet order (fs17_00000...),
exactly the V1.6 merge discipline. Refuses on any missing text.

  python tools/merge_foreign17.py
Then re-hash before any seal run.
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "results" / "v17" / "data"
ADIR = Path(r"C:\Users\admin\AppData\Local\Temp\claude"
            r"\C--Users-admin-Downloads"
            r"\b3339104-bde3-44e9-979e-e645141d4320\scratchpad"
            r"\v17_author")


def main():
    sheets = json.loads((DATA / "factsheets17.json")
                        .read_text(encoding="utf-8"))
    assign = json.loads((ADIR / "assignment.json")
                        .read_text(encoding="utf-8"))
    texts = {}
    for p in sorted(ADIR.glob("authored_*.json")):
        for row in json.loads(p.read_text(encoding="utf-8")):
            texts[row["sheet_id"]] = row["text"].strip()
    missing = [s["sheet_id"] for s in sheets
               if s["sheet_id"] not in texts]
    if missing:
        print("REFUSING: %d sheets lack text" % len(missing))
        sys.exit(1)

    ordered = sorted(sheets, key=lambda s: s["sheet_id"])
    si = 0
    replaced = Counter()
    for split in ("acq", "dev", "seal", "replay"):
        p = DATA / ("q1m_%s.jsonl" % split)
        out_lines = []
        with open(p, encoding="utf-8") as f:
            for line in f:
                it = json.loads(line)
                if it.get("register") == "foreign_slot":
                    s = ordered[si]
                    si += 1
                    it = {"id": it["id"], "text": texts[s["sheet_id"]],
                          "plan": s["plan"], "gold": s["gold"],
                          "gold_type": s["gold_type"], "k": s["k"],
                          "leaves": s["leaves"],
                          "nonmono": s["nonmono"],
                          "multidomain": s["multidomain"],
                          "register": "foreign",
                          "author": assign[s["sheet_id"]],
                          "sheet_id": s["sheet_id"],
                          "distractor": False, "sig": s["sig"]}
                    replaced[split] += 1
                out_lines.append(json.dumps(it))
        p.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    assert si == len(ordered), "slot/sheet count mismatch: %d" % si
    print(json.dumps({"replaced": dict(replaced),
                      "authors": dict(Counter(assign.values()))}))


if __name__ == "__main__":
    main()
