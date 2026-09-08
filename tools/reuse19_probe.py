# -*- coding: utf-8 -*-
"""POST-HOC analysis (after v1.9-final; nothing served): "suggest, don't serve".

For every SEALED item, every A2-admitted reading of ANOTHER item with the
same cue key is a CANDIDATE (impure keys included).  Each candidate is
bound, gated and executed exactly as a fresh reading would be; it is
ADMITTED only if its value agrees with the escalation model's OWN answer
to the item.  Admitted values are graded by gold.  Variants:
  P0  candidate agrees with own answer (no engine gates)
  P1  candidate passes G-P6 + structural rules AND agrees (A2 on reuse)
Also reports the overlap with the fresh-reading A2 wrongs (shared-prior
items where the own answer itself is wrong).
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import reader19v as V  # noqa: E402
import reader19 as S1  # noqa: E402

OUT = V.OUT


def probe(model, phases=("dev", "sealed"), tag=""):
    lib = []
    for phase in phases:
        rp = OUT / ("M-%s_%s_rows.json" % (model, phase))
        if not rp.exists():
            continue
        rows = {r["id"]: r for r in json.loads(rp.read_text(encoding="utf-8"))}
        items = {it["id"]: it for it in V._load_items(phase)}
        readings = V._load_readings(model, phase)
        for iid, r in rows.items():
            if r.get("A2"):
                lib.append({"donor": iid, "key": r["key"],
                            "plan": readings[iid]["plan"],
                            "n": len(items[iid]["numbers"])})
    by_key = defaultdict(list)
    for t in lib:
        by_key[t["key"]].append(t)
    sealed = V._load_items("sealed")
    answers = V._load_answers(model, "sealed")
    fresh = {r["id"]: r for r in json.loads((OUT / ("M-%s_sealed_rows.json" % model)).read_text(encoding="utf-8"))}
    fresh_a2_wrong = {i for i, r in fresh.items() if r.get("A2") and not r.get("correct", r.get("reading_correct", True))}
    st = Counter()
    res = {"P0": {"served": 0, "correct": 0, "WRONG": 0, "wrong": []},
           "P1": {"served": 0, "correct": 0, "WRONG": 0, "wrong": []}}
    per_item_cands = []
    for it in sealed:
        cands = [t for t in by_key.get(it["key"], []) if t["donor"] != it["id"] and t["n"] == len(it["numbers"])]
        if not cands:
            continue
        st["items_with_candidate"] += 1
        per_item_cands.append(len(cands))
        own = S1.parse_answer(answers.get(it["id"]))
        gold = S1.parse_answer(it["gold"])
        if own is None:
            st["no_own_answer"] += 1
            continue
        executed = 0
        agree0 = []   # (value, donor) agreeing with own answer, any gates
        agree1 = []   # agreeing AND passing G-P6 + rules
        for t in cands:
            row = V.stage(it, {"plan": t["plan"]})
            if row["status"] != "executed":
                continue
            executed += 1
            if S1.close(row["value"], own):
                agree0.append((row["value"], t["donor"]))
                if row["g6"] and not row["rule"]:
                    agree1.append((row["value"], t["donor"]))
        st["items_with_executed_candidate"] += bool(executed)
        st["candidates_executed"] += executed
        for name, ag in (("P0", agree0), ("P1", agree1)):
            if not ag:
                continue
            v, donor = ag[0]
            res[name]["served"] += 1
            res[name].setdefault("served_rows", []).append({"id": it["id"], "n_numbers": len(it["numbers"]), "fresh": fresh.get(it["id"], {}).get("status"), "fresh_A2": bool(fresh.get(it["id"], {}).get("A2")), "donor": donor, "correct": S1.close(v, gold)})
            res[name].setdefault("served_by_fresh_status", Counter())[fresh.get(it["id"], {}).get("status", "?") + ("" if not fresh.get(it["id"], {}).get("A2") else "+A2")] += 1
            if S1.close(v, gold):
                res[name]["correct"] += 1
            else:
                res[name]["WRONG"] += 1
                res[name]["wrong"].append({"id": it["id"], "donor": donor, "key": it["key"],
                                           "value": v, "own": own, "gold": it["gold"],
                                           "fresh_A2_wrong": it["id"] in fresh_a2_wrong,
                                           "fresh_status": fresh.get(it["id"], {}).get("status")})
    for name in ("P0", "P1"):
        r = res[name]
        r["FALSE_ADMIT"] = round(r["WRONG"] / r["served"], 4) if r["served"] else None
        r["wrong_ids"] = sorted(w["id"] for w in r["wrong"])
        r["wrong_also_fresh_A2_wrong"] = sum(w["fresh_A2_wrong"] for w in r["wrong"])
        r["served_by_fresh_status"] = dict(r.get("served_by_fresh_status", {}))
        r["served_zero_slot"] = sum(1 for x in r.get("served_rows", []) if x["n_numbers"] == 0)
        r["wrong_zero_slot"] = sum(1 for x in r.get("served_rows", []) if x["n_numbers"] == 0 and not x["correct"])
        r["served_fresh_null_or_killed"] = sum(1 for x in r.get("served_rows", []) if x["fresh"] != "executed")
        r["wrong_fresh_null_or_killed"] = sum(1 for x in r.get("served_rows", []) if x["fresh"] != "executed" and not x["correct"])
    # how many reuse serves land on items the fresh reading could NOT serve (real coverage gain)
    for name in ("P0", "P1"):
        pass
    out = {"model": model, "library": len(lib), "keys": len(by_key),
           "counts": dict(st),
           "candidates_per_item_mean": round(sum(per_item_cands) / len(per_item_cands), 2) if per_item_cands else 0,
           "fresh_A2_wrong_ids": sorted(fresh_a2_wrong),
           "P0": res["P0"], "P1": res["P1"]}
    (OUT / ("reuse19_probe_M-%s%s.json" % (model, tag))).write_text(json.dumps(out, indent=1), encoding="utf-8")
    slim = {k: (v if k not in ("P0", "P1") else {kk: vv for kk, vv in v.items() if kk not in ("wrong", "served_rows")}) for k, v in out.items()}
    print(json.dumps(slim, indent=1))
    return out


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "sonnet"
    if len(sys.argv) > 2 and sys.argv[2] == "devlib":
        probe(m, phases=("dev",), tag="_devlib")
    else:
        probe(m)
