# -*- coding: utf-8 -*-
# origin: new for V1.7 -- Phase L' free-hand minting (SPEC 4.1)
"""Prep and gauntlet for the three V1.7 candidate classes.

  python tools/mint17.py prep --cap 2000
      ESCALATED in-domain ACQ items -> per-model offer chunks
      (same sample for every model; text only; distractors excluded).

  python tools/mint17.py gauntlet --model <m>
      Reads candidates_<m>_*.json. Class by shape:
        parse:     {"name","pattern","task"}          (V1.6 class)
        chain:     {"name","pattern","plan"}          plan nodes may
                   use "$group" captures in slot values
        connector: {"name","from_unit","to_unit","adapter"}
                   adapter is an expression over $v (upstream value),
                   e.g. "($v)/1000"; certifies queries where the
                   deterministic chain died ONLY on a final-unit
                   mismatch between from_unit and to_unit.
      Every class faces chained probation: >=3 correct end-to-end
      witnessed serves, >=2 distinct operand tuples, ZERO wrong
      (one wrong = dead). Ledger per class per model.
"""
import argparse
import json
import random
import re
from re import error
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))

SCRATCH = Path(r"C:\Users\admin\AppData\Local\Temp\claude"
               r"\C--Users-admin-Downloads"
               r"\b3339104-bde3-44e9-979e-e645141d4320\scratchpad"
               r"\v17_mint")
MODELS = ["haiku", "sonnet", "opus", "fable"]
DATA = HERE / "results" / "v17" / "data"
RES = HERE / "results" / "v17"


def _load_split(name):
    out = {}
    with open(DATA / ("q1m_%s.jsonl" % name), encoding="utf-8") as f:
        for line in f:
            it = json.loads(line)
            out[it["id"]] = it
    return out


def prep(cap):
    items = _load_split("acq")
    resid = []
    with open(RES / "det_acq.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("served"):
                continue
            it = items.get(r["id"])
            if it is None or it.get("distractor"):
                continue
            resid.append(it)
    rng = random.Random(1703)
    rng.shuffle(resid)
    sample = resid[:cap]
    SCRATCH.mkdir(parents=True, exist_ok=True)
    offers = [{"k": it.get("k"), "text": it["text"]} for it in sample]
    for m in MODELS:
        ch = (len(offers) + 4) // 5
        for ci in range(5):
            (SCRATCH / ("offers_%s_%d.json" % (m, ci))).write_text(
                json.dumps(offers[ci * ch:(ci + 1) * ch], indent=0),
                encoding="utf-8")
    (SCRATCH / "sample_ids.json").write_text(
        json.dumps([it["id"] for it in sample]), encoding="utf-8")
    print(json.dumps({"residuals": len(resid),
                      "offered": len(sample)}))


def _classify(cand):
    if "task" in cand:
        return "parse"
    if "plan" in cand:
        return "chain"
    if "adapter" in cand:
        return "connector"
    return None


def _sub_plan(plan_t, m):
    """Substitute $group captures into a plan template."""
    def sub_val(v):
        if isinstance(v, str):
            bad = []

            def rep(mm):
                try:
                    g = m.group(mm.group(1))
                except (IndexError, error):
                    bad.append(1)
                    return ""
                if g is None:
                    bad.append(1)
                    return ""
                return g.strip()
            s = re.sub(r"\$([A-Za-z_]\w*)", rep, v)
            if bad:
                raise ValueError("missing capture")
            if re.fullmatch(r"-?\d+(?:\.\d+)?", s):
                return float(s)
            return s
        return v
    nodes = []
    for n in plan_t.get("nodes", []):
        nodes.append({k: sub_val(v) for k, v in n.items()})
    return {"nodes": nodes, "final": plan_t.get("final")}


def gauntlet(model):
    import v17_run as RUN
    from reflex import (acquire16, chainexec17, composer17,
                        plangate17, sciparse16)
    cands = []
    for ci in range(5):
        p = SCRATCH / ("candidates_%s_%d.json" % (model, ci))
        if p.exists():
            try:
                cands.extend(json.loads(p.read_text(encoding="utf-8")))
            except json.JSONDecodeError as e:
                print("chunk %d unparseable: %s" % (ci, e))
    items = _load_split("acq")
    sample_ids = json.loads((SCRATCH / "sample_ids.json")
                            .read_text(encoding="utf-8"))
    probation = [items[i] for i in sample_ids if i in items]

    ledger = Counter()
    kills, admitted = [], []
    for cand in cands:
        cls = _classify(cand)
        ledger["proposed"] += 1
        ledger["proposed_%s" % cls] += 1
        if cls is None:
            ledger["g1_killed"] += 1
            kills.append({"name": cand.get("name"),
                          "why": "g1: unknown class"})
            continue
        if cls == "parse":
            adm, led, kl = acquire16.gauntlet(
                [cand], [(it, it["text"]) for it in probation
                         if it.get("gold_type") == "num" and
                         it.get("k") == 2],
                lambda it, v: RUN.grade(it, v))
            for k in ("g1_killed", "g2_killed", "g3_inert",
                      "g3_memorize", "g3_wrong"):
                ledger[k] += led[k]
            kills.extend(kl)
            if adm:
                a = adm[0]
                a["cls"] = "parse"
                admitted.append(a)
                ledger["admitted"] += 1
                ledger["admitted_parse"] += 1
            continue
        if cls == "chain":
            pat = cand.get("pattern") or ""
            try:
                rx = re.compile(pat, re.I)
            except re.error as e:
                ledger["g1_killed"] += 1
                kills.append({"name": cand.get("name"),
                              "why": "g1: regex: %s" % e})
                continue
            serves, tuples, dead = [], set(), None
            for it in probation:
                m = rx.search(it["text"])
                if not m or m.start() > 12:
                    continue
                try:
                    plan = _sub_plan(cand["plan"], m)
                except (ValueError, KeyError):
                    continue
                ok, _t = plangate17.check(plan, it["text"])
                if not ok:
                    continue
                v, cert = chainexec17.run(plan)
                if v is None:
                    continue
                if it.get("gold_type") == "bool":
                    v = v > 0
                good = RUN.grade(it, v)
                serves.append(it["id"])
                tuples.add(tuple(sorted(
                    (k2, str(v2)) for n in plan["nodes"]
                    for k2, v2 in n.items() if k2 not in ("id",))))
                if not good:
                    dead = "g3: WRONG chain serve on %s" % it["id"]
                    break
            if dead:
                ledger["g3_wrong"] += 1
                kills.append({"name": cand.get("name"), "why": dead})
            elif len(serves) < 3:
                ledger["g3_inert"] += 1
                kills.append({"name": cand.get("name"),
                              "why": "g3: inert (%d)" % len(serves)})
            elif len(tuples) < 2:
                ledger["g3_memorize"] += 1
                kills.append({"name": cand.get("name"),
                              "why": "g3: memorization"})
            else:
                admitted.append({"cls": "chain",
                                 "name": cand.get("name"),
                                 "pattern": pat,
                                 "plan": cand["plan"],
                                 "probation": len(serves)})
                ledger["admitted"] += 1
                ledger["admitted_chain"] += 1
            continue
        # connector: repair items whose composer plan died only on the
        # final-unit mismatch from_unit -> to_unit
        fu, tu = cand.get("from_unit"), cand.get("to_unit")
        adapter = cand.get("adapter") or ""
        if not fu or not tu or "$v" not in adapter:
            ledger["g1_killed"] += 1
            kills.append({"name": cand.get("name"),
                          "why": "g1: malformed connector"})
            continue
        serves, tuples, dead = [], set(), None
        for it in probation:
            plan = composer17.parse_chain(it["text"])
            if plan is None:
                continue
            ok, t = plangate17.check(plan, it["text"])
            if ok:
                continue          # nothing to repair
            kill = (t[-1].get("kill") or "")
            if ("asked in" not in kill) or (repr(fu) not in kill):
                continue
            if repr(tu) not in kill.split(";")[0] and \
                    "'%s'" % tu not in kill:
                pass
            last = plan["nodes"][-1]["id"]
            nid = "n%d" % (len(plan["nodes"]) + 1)
            plan2 = {"nodes": plan["nodes"] + [
                {"id": nid, "op": "evaluate",
                 "expr": adapter.replace("$v", "@" + last),
                 "unit": tu}], "final": nid}
            ok2, _t2 = plangate17.check(plan2, it["text"])
            if not ok2:
                continue
            v, cert = chainexec17.run(plan2)
            if v is None:
                continue
            good = RUN.grade(it, v)
            serves.append(it["id"])
            tuples.add(round(float(v), 6))
            if not good:
                dead = "g3: WRONG connector serve on %s" % it["id"]
                break
        if dead:
            ledger["g3_wrong"] += 1
            kills.append({"name": cand.get("name"), "why": dead})
        elif len(serves) < 3:
            ledger["g3_inert"] += 1
            kills.append({"name": cand.get("name"),
                          "why": "g3: inert (%d)" % len(serves)})
        elif len(tuples) < 2:
            ledger["g3_memorize"] += 1
            kills.append({"name": cand.get("name"),
                          "why": "g3: single value (memorization)"})
        else:
            admitted.append({"cls": "connector",
                             "name": cand.get("name"),
                             "from_unit": fu, "to_unit": tu,
                             "adapter": adapter,
                             "probation": len(serves)})
            ledger["admitted"] += 1
            ledger["admitted_connector"] += 1

    led = dict(ledger)
    led["model"] = model
    (RES / ("reflexlib17_%s.json" % model)).write_text(
        json.dumps(admitted, indent=1), encoding="utf-8")
    (RES / ("mint_ledger17_%s.json" % model)).write_text(
        json.dumps({"ledger": led, "kills": kills}, indent=1),
        encoding="utf-8")
    print(json.dumps(led, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "gauntlet"])
    ap.add_argument("--cap", type=int, default=2000)
    ap.add_argument("--model", default=None,
                    choices=MODELS + ["all", None])
    a = ap.parse_args()
    if a.cmd == "prep":
        prep(a.cap)
    else:
        gauntlet(a.model)


if __name__ == "__main__":
    main()
