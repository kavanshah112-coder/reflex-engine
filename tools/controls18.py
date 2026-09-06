# -*- coding: utf-8 -*-
# origin: new for V1.8 -- the positive/negative control batteries (SPEC 4.5, 9 GATE-CTRL)
"""Every battery must pass before any counting run; results are
written to results/v18/controls18.json and printed.

  python tools/controls18.py [--lib results/v18/planlib18_all_all.json]

Batteries:
  gates      plangate17, chainexec17 and plangate18 control batteries
             (V1.7's must still hold; G-P4' dual-role/order/benign-
             repeat; G-P5 amount-for-interest; pre-differentiation)
  haiku13    the 13 certified-wrong haiku sealed plans through
             plangate18: 13/13 must die (12 at G-P5, 1 at G-P4')
  probe_b32  the 8,842 V1.7 wrong serves through binder18 over the
             given library: every row abstains or serves the gold;
             one served-wrong fails the battery
  harvest_neg every certified-wrong / gate-killed V1.7 plan pushed
             through harvest18.templateize: none may enter a library
             (checked by donor id against the library's donors)
  repro      byte-exact V1.7 reproduction: v18_run --gate17 rows vs
             results/v17/det_dev.jsonl on the same ids
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))
V17 = HERE / "results" / "v17"
OUT = HERE / "results" / "v18"


def gates():
    from reflex import chainexec17, plangate17, plangate18
    ok1, f1 = plangate17.control_battery()
    ok3, f3 = plangate18.control_battery()
    try:
        ok2, f2 = chainexec17.gate_control()
    except Exception as exc:                 # noqa: BLE001
        ok2, f2 = False, [repr(exc)]
    return {"plangate17": ok1, "chainexec17": ok2, "plangate18": ok3,
            "fails": [str(x) for x in (f1 + f3 + (f2 or []))],
            "pass": ok1 and ok2 and ok3}


def haiku13():
    from reflex import plangate18
    rows = json.loads((OUT / "probe_haiku13.json").read_text(
        encoding="utf-8"))["rows"]
    killed = Counter()
    passed = []
    for r in rows:
        ok, t = plangate18.check(r["plan"], r["text"])
        if ok:
            passed.append(r["id"])
        else:
            killed[t[-1].get("gate")] += 1
    return {"n": len(rows), "killed_by": dict(killed),
            "passed": passed, "pass": not passed}


def probe_b32(lib_paths):
    import v17_run as RUN
    from reflex import binder18
    lib = binder18.Library.load(lib_paths)
    rows = json.loads((OUT / "probe_b32.json").read_text(
        encoding="utf-8"))["rows"]
    st = Counter()
    served_wrong = []
    reasons = Counter()
    for r in rows:
        v, cert, info = binder18.serve(r["text"], lib, qid=r["id"])
        if v is None:
            st["abstained"] += 1
            reasons[(info["reason"] or "?").split(":")[0]] += 1
            continue
        g = (v > 0) if r["gold_type"] == "bool" else v
        if RUN.grade(r, g):
            st["served_gold"] += 1
        else:
            st["SERVED_WRONG"] += 1
            served_wrong.append({"id": r["id"], "model": r["model"],
                                 "value": v, "gold": r["gold"],
                                 "template": info["template"]})
    return {"n": len(rows), "lib": lib_paths, "templates": len(lib),
            "counts": dict(st), "abstain_reasons": dict(reasons),
            "served_wrong": served_wrong, "pass": not served_wrong}


def harvest_neg(lib_paths):
    import zipfile
    import harvest18 as H
    from reflex import binder18
    lib = binder18.Library.load(lib_paths)
    donors = lib.donors
    z = zipfile.ZipFile(V17 / "v17_plan_archive.zip")
    items = H._load_items(["dev", "seal"])
    st = Counter()
    leaked = []
    for m in H.MODELS:
        for ph in ("dev", "sealed"):
            scored = json.loads((V17 / ("plans_%s_%s.json" % (m, ph)))
                                .read_text(encoding="utf-8"))
            for r in scored["rows"]:
                if r.get("correct") is True:
                    continue
                st["bad_plans"] += 1
                name = "plans_%s_%s/plan_%s.json" % (m, ph, r["id"])
                try:
                    plan = json.loads(z.read(name).decode("utf-8"))
                except KeyError:
                    st["archive_missing"] += 1
                    continue
                it = items.get(r["id"])
                if it is None or not isinstance(plan, dict):
                    st["unusable"] += 1
                    continue
                tpl, why = H.templateize(it["text"], plan)
                st["templatized" if tpl else "rejected"] += 1
                if r["id"] in donors:
                    # a bad plan's donor may also have donated a GOOD
                    # plan from another model; the leak test is on the
                    # plan, so compare plans
                    for t in lib.templates:
                        if r["id"] in t["donors"] and tpl and \
                                json.dumps(H._norm_plan(tpl["plan"]),
                                           sort_keys=True) == \
                                json.dumps(t["plan"], sort_keys=True):
                            leaked.append({"id": r["id"], "model": m,
                                           "template": t["name"]})
    return {"counts": dict(st), "leaked": leaked, "pass": not leaked}


def repro():
    a = {}
    with open(OUT / "det17chk_dev.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            a[r["id"]] = r
    diffs = 0
    n = 0
    with open(V17 / "det_dev.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["id"] not in a:
                continue
            n += 1
            b = a[r["id"]]
            if (r.get("path"), r.get("served"), r.get("correct")) != \
                    (b.get("path"), b.get("served"), b.get("correct")):
                diffs += 1
    return {"compared": n, "diffs": diffs, "pass": diffs == 0 and n > 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", nargs="*",
                    default=[str(OUT / "planlib18_all_all.json")])
    ap.add_argument("--skip", nargs="*", default=[])
    a = ap.parse_args()
    res = {}
    for name, fn, args in [("gates", gates, ()),
                           ("haiku13", haiku13, ()),
                           ("harvest_neg", harvest_neg, (a.lib,)),
                           ("probe_b32", probe_b32, (a.lib,)),
                           ("repro", repro, ())]:
        if name in a.skip:
            continue
        try:
            res[name] = fn(*args)
        except Exception as exc:             # noqa: BLE001
            res[name] = {"error": repr(exc), "pass": False}
        print(name, "PASS" if res[name].get("pass") else "FAIL",
              json.dumps({k: v for k, v in res[name].items()
                          if k not in ("served_wrong", "leaked",
                                       "fails")})[:400])
    res["ALL_PASS"] = all(v.get("pass") for v in res.values())
    (OUT / "controls18.json").write_text(json.dumps(res, indent=1),
                                         encoding="utf-8")
    print("GATE-CTRL:", "PASS" if res["ALL_PASS"] else "FAIL")


if __name__ == "__main__":
    main()
