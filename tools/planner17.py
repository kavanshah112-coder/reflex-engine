# -*- coding: utf-8 -*-
# origin: new for V1.7 -- the planner + time-to-structure campaign
"""S-PLAN sampling, batch staging, and scoring for model-proposed
plans (SPEC 5, 6).

  python tools/planner17.py prep --phase dev   (after det dev run)
  python tools/planner17.py prep --phase sealed (after det seal run)
      Samples escalated 3+-step in-domain items (600 dev / 1,200
      sealed), same items for every model minus self-authored foreign
      items; stages batches of 25 as batch_<model>_<phase>_<i>.json.

  python tools/planner17.py score --model <m> --phase <phase>
      Reads plan_<id>.json files from that model's output dir; the
      per-file mtime DELTAS are the per-item structure-finding times
      (harness-observed, never self-reported). Each plan runs the
      gate; gate-passing plans execute via chainexec17 and are graded.
      Admitted (gate-pass AND correct) plans are generalized into a
      REPLAY library entry keyed by structure trigger... first
      version: exact-plan replay only on the planned item; the replay
      LIBRARY is built by tools/planlib17.py from admitted plans.
      Writes results/v17/plans_<model>_<phase>.json with per-depth
      timing distributions, validity, correctness, SAFETY-3 counter.
"""
import argparse
import json
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))

SCRATCH = Path(r"C:\Users\admin\AppData\Local\Temp\claude"
               r"\C--Users-admin-Downloads"
               r"\b3339104-bde3-44e9-979e-e645141d4320\scratchpad"
               r"\v17_plan")
MODELS = ["haiku", "sonnet", "opus", "fable"]
DATA = HERE / "results" / "v17" / "data"
RES = HERE / "results" / "v17"
BATCH = 25


def _load_split(name):
    out = {}
    with open(DATA / ("q1m_%s.jsonl" % name), encoding="utf-8") as f:
        for line in f:
            it = json.loads(line)
            out[it["id"]] = it
    return out


def prep(phase):
    split = "dev" if phase == "dev" else "seal"
    n_want = 600 if phase == "dev" else 1200
    items = _load_split(split)
    pool = []
    with open(RES / ("det_%s.jsonl" % split), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("served"):
                continue
            it = items.get(r["id"])
            if it is None or it.get("distractor") or \
                    (it.get("k") or 0) < 3:
                continue
            pool.append(it)
    rng = random.Random(1704 if phase == "dev" else 1705)
    rng.shuffle(pool)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for m in MODELS:
        picked, i = [], 0
        while len(picked) < n_want and i < len(pool):
            it = pool[i]
            i += 1
            if it.get("register") == "foreign" and \
                    it.get("author") == m:
                continue
            picked.append(it)
        outdir = SCRATCH / ("plans_%s_%s" % (m, phase))
        outdir.mkdir(parents=True, exist_ok=True)
        nb = 0
        for bi in range(0, len(picked), BATCH):
            b = picked[bi:bi + BATCH]
            (SCRATCH / ("batch_%s_%s_%02d.json" % (m, phase,
                                                   bi // BATCH))
             ).write_text(json.dumps(
                 [{"id": it["id"], "k": it["k"],
                   "question": it["text"]} for it in b], indent=0),
                 encoding="utf-8")
            nb += 1
        manifest["%s_%s" % (m, phase)] = {"items": len(picked),
                                          "batches": nb}
    (SCRATCH / ("manifest_%s.json" % phase)).write_text(
        json.dumps(manifest), encoding="utf-8")
    print(json.dumps({"pool": len(pool), "batches": manifest}))


def score(model, phase):
    import v17_run as RUN
    from reflex import chainexec17, plangate17
    split = "dev" if phase == "dev" else "seal"
    items = _load_split(split)
    outdir = SCRATCH / ("plans_%s_%s" % (model, phase))
    files = sorted(outdir.glob("plan_*.json"),
                   key=lambda p: p.stat().st_mtime)
    per_k_times = defaultdict(list)
    st = Counter()
    rows = []
    prev_mtime = None
    batch_boundaries = {}
    # per-batch first item has no delta (agent startup); mark batches
    for bf in SCRATCH.glob("batch_%s_%s_*.json" % (model, phase)):
        b = json.loads(bf.read_text(encoding="utf-8"))
        if b:
            batch_boundaries[b[0]["id"]] = True
    admitted_plans = []
    for p in files:
        iid = p.stem[5:]
        it = items.get(iid)
        if it is None:
            continue
        mtime = p.stat().st_mtime
        dt = None
        if prev_mtime is not None and iid not in batch_boundaries:
            dt = mtime - prev_mtime
        prev_mtime = mtime
        st["returned"] += 1
        try:
            plan = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(plan, dict) and "plan" in plan:
                plan = plan["plan"]
        except json.JSONDecodeError:
            st["unparseable"] += 1
            continue
        ok, transcript = plangate17.check(plan, it["text"])
        row = {"id": iid, "k": it.get("k"), "gate": ok, "dt": dt}
        if dt is not None:
            per_k_times["k%s" % it.get("k")].append(dt)
        if not ok:
            st["gate_killed"] += 1
            row["kill"] = transcript[-1].get("kill")
            rows.append(row)
            continue
        v, cert = chainexec17.run(plan)
        if v is None:
            st["exec_refused"] += 1
            rows.append(row)
            continue
        vv = (v > 0) if it.get("gold_type") == "bool" else v
        good = RUN.grade(it, vv)
        st["served"] += 1
        st["correct" if good else "SAFETY3_WRONG"] += 1
        row["correct"] = good
        rows.append(row)
        if good:
            admitted_plans.append({"id": iid, "sig": it.get("sig"),
                                   "k": it.get("k"), "plan": plan})
    timing = {}
    for k, ts in sorted(per_k_times.items()):
        ts = sorted(ts)
        timing[k] = {"n": len(ts),
                     "median_s": round(statistics.median(ts), 2),
                     "p90_s": round(ts[int(0.9 * (len(ts) - 1))], 2)
                     if ts else None,
                     "mean_s": round(statistics.mean(ts), 2)}
    out = {"model": model, "phase": phase, "n_files": len(files),
           "stats": dict(st), "timing_by_k": timing,
           "timing_note": "per-item deltas of harness-observed file "
                          "mtimes; first item of each batch excluded "
                          "(agent startup)"}
    (RES / ("plans_%s_%s.json" % (model, phase))).write_text(
        json.dumps({"summary": out, "rows": rows}, indent=1),
        encoding="utf-8")
    (RES / ("planlib_%s_%s.json" % (model, phase))).write_text(
        json.dumps(admitted_plans, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "score"])
    ap.add_argument("--phase", choices=["dev", "sealed"],
                    required=True)
    ap.add_argument("--model", choices=MODELS, default=None)
    a = ap.parse_args()
    if a.cmd == "prep":
        prep(a.phase)
    else:
        score(a.model, a.phase)


if __name__ == "__main__":
    main()
