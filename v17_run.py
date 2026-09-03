# -*- coding: utf-8 -*-
# origin: new for V1.7 -- the evaluation runner (SPEC 8, 9)
"""One arm over one split of Q-1M.

  python v17_run.py --split dev [--data results/v17/data] [--limit N]
                    [--arm det] [--plans plans.json]

Arms:
  det        gateway16 (V1.6 serving incl. the frozen 271-reflex
             library) first; if ESCALATED, composer17 -> plan gate ->
             chainexec17 (per-step witness + end-to-end witness).
  plan-...   same, plus a PLAN LIBRARY (--plans): admitted model
             plans keyed by structure trigger; tried only after the
             deterministic paths escalate, through the same gate and
             executors (SPEC 5: plan replay).

Counters follow v16_run's shape plus chain-specific ones. A served
answer with no gate transcript, or a distractor served, or an
unaddressed step, counts against SAFETY exactly as SPEC 9 says.
"""
import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))


def grade(it, val):
    gt = it["gold_type"]
    try:
        if gt == "bool":
            if isinstance(val, bool):
                return val == bool(it["gold"])
            if isinstance(val, (int, float)):
                return (val > 0) == bool(it["gold"])
            return False
        v, g = float(val), float(it["gold"])
        return abs(v - g) <= max(1e-4 * abs(g), 1e-6)
    except (TypeError, ValueError):
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev",
                    choices=["acq", "dev", "seal", "replay"])
    ap.add_argument("--data", default=str(HERE / "results" / "v17" /
                                          "data"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--arm", default="det")
    ap.add_argument("--tag", default="")
    ap.add_argument("--plans", default=None,
                    help="admitted plan library (from planner17)")
    ap.add_argument("--mintlib", default=None,
                    help="V1.7 minted library (reflexlib17_*.json): "
                         "parse/chain reflexes tried after the "
                         "composer escalates; connectors repair "
                         "final-unit gate kills")
    ap.add_argument("--reflexlib", default=str(
        HERE / "results" / "v16" / "reflexlib_all.json"))
    a = ap.parse_args()

    items = []
    with open(Path(a.data) / ("q1m_%s.jsonl" % a.split),
              encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < a.offset:
                continue
            items.append(json.loads(line))
            if a.limit and len(items) >= a.limit:
                break

    from reflex import acquire16, chainexec17, composer17, plangate17
    from reflex.gateway16 import ask16

    # B30: on merged foreign chains, V1.6's single-step parser served
    # the FIRST sub-question's value as the whole answer (5 wrongs at
    # 8e-05/2.7e-05 on dev/acq — "Compute 4*(6+7). With this as
    # principal ..." served 52 = step one). Chain-marked text is out
    # of the single-step engine's domain BY DEFINITION: a partial
    # answer to a chain is a wrong answer, so such text never reaches
    # the V1.6 path — it belongs to the composer, minted chains, and
    # plans. Markers: a result-reference or sequential connective
    # after the first clause.
    import re as _re30
    CHAIN_MARKED = _re30.compile(
        r"\b(?:with (?:this|it|that)\b|from this\b|"
        r"using (?:this|that|it)\b|the (?:result|interest|difference|"
        r"count|sum|total|value)\b.*\b(?:then|multiply|subtract|add|"
        r"divide)|then\b|; )", _re30.I)

    library = json.loads(Path(a.reflexlib).read_text(
        encoding="utf-8")) if a.reflexlib and \
        Path(a.reflexlib).exists() else []
    plan_lib = []
    if a.plans:
        plan_lib = json.loads(Path(a.plans).read_text(
            encoding="utf-8"))
    mint_parse, mint_chain, mint_conn = [], [], []
    if a.mintlib:
        for c in json.loads(Path(a.mintlib).read_text(
                encoding="utf-8")):
            {"parse": mint_parse, "chain": mint_chain,
             "connector": mint_conn}.get(c.get("cls"), []).append(c)
    import re as _re
    from mint17 import _sub_plan as _mint_sub

    st = Counter()
    by_k = defaultdict(Counter)
    wrong_rows, safety2 = [], []
    rows = []
    t0 = time.perf_counter()
    for it in items:
        text = it["text"]
        served = None
        path = None
        try:
            chainish = bool(CHAIN_MARKED.search(text)) or \
                text.count(". ") >= 2
            if not chainish:
                r = ask16(text, it["id"])
                if r["status"] == "SERVED":
                    served, path = r["value"], "v16:" + r["path"]
                elif r["status"] == "ESCALATED" and library:
                    hit = acquire16.apply_library(text, library)
                    if hit is not None:
                        served, path = hit["value"], "v16:reflex"
            comp_kill = None
            comp_plan = None
            if served is None:
                comp_plan = composer17.parse_chain(text)
                if comp_plan is not None:
                    ok, transcript = plangate17.check(comp_plan, text)
                    if ok:
                        v, cert = chainexec17.run(comp_plan)
                        if v is not None:
                            served, path = v, "chain:composer"
                            st["chain_served"] += 1
                    else:
                        st["gate_killed"] += 1
                        comp_kill = (transcript[-1].get("kill") or "")
            if served is None and mint_parse:
                hit = acquire16.apply_library(text, mint_parse)
                if hit is not None:
                    served, path = hit["value"], "mint:parse"
                    st["mint_served"] += 1
            if served is None and mint_chain:
                for cand in mint_chain:
                    rx = cand.get("_rx")
                    if rx is None:
                        try:
                            rx = _re.compile(cand["pattern"], _re.I)
                        except _re.error:
                            continue
                        cand["_rx"] = rx
                    m = rx.search(text)
                    if not m or m.start() > 12:
                        continue
                    try:
                        plan = _mint_sub(cand["plan"], m)
                    except (ValueError, KeyError):
                        continue
                    ok, _t = plangate17.check(plan, text)
                    if not ok:
                        continue
                    v, cert = chainexec17.run(plan)
                    if v is not None:
                        served, path = v, "mint:chain:%s" % \
                            cand.get("name")
                        st["mint_served"] += 1
                        break
            if served is None and mint_conn and comp_kill and \
                    comp_plan is not None and "asked in" in comp_kill:
                for cand in mint_conn:
                    if repr(cand["from_unit"]) not in comp_kill and \
                            "'%s'" % cand["from_unit"] not in comp_kill:
                        continue
                    last = comp_plan["nodes"][-1]["id"]
                    nid = "n%d" % (len(comp_plan["nodes"]) + 1)
                    plan2 = {"nodes": comp_plan["nodes"] + [
                        {"id": nid, "op": "evaluate",
                         "expr": cand["adapter"].replace(
                             "$v", "@" + last),
                         "unit": cand["to_unit"]}], "final": nid}
                    ok, _t = plangate17.check(plan2, text)
                    if not ok:
                        continue
                    v, cert = chainexec17.run(plan2)
                    if v is not None:
                        served, path = v, "mint:connector:%s" % \
                            cand.get("name")
                        st["mint_served"] += 1
                        break
            if served is None and plan_lib:
                for cand in plan_lib:
                    import re as _re
                    m = _re.search(cand["trigger"], text, _re.I)
                    if not m:
                        continue
                    plan = json.loads(_re.sub(
                        r"\$(\w+)", lambda mm: m.group(mm.group(1)),
                        json.dumps(cand["plan"])))
                    ok, transcript = plangate17.check(plan, text)
                    if not ok:
                        continue
                    v, cert = chainexec17.run(plan)
                    if v is not None:
                        served, path = v, "chain:plan:%s" % \
                            cand.get("model", "?")
                        st["plan_served"] += 1
                        break
        except Exception as exc:            # noqa: BLE001  (B27)
            st["engine_error"] += 1
            path = "engine-error:%s" % type(exc).__name__
        rec = {"id": it["id"], "k": it.get("k"),
               "path": path, "served": served is not None}
        if served is not None:
            if it.get("distractor"):
                st["SAFETY2_SERVED"] += 1
                safety2.append(it["id"])
                rec["correct"] = False
            else:
                if it["gold_type"] == "bool" and \
                        isinstance(served, float) and \
                        path and path.startswith("chain"):
                    served_g = served > 0
                else:
                    served_g = served
                ok = grade(it, served_g)
                st["served"] += 1
                st["correct" if ok else "WRONG"] += 1
                kk = "k%s" % it.get("k")
                by_k[kk]["served"] += 1
                by_k[kk]["correct" if ok else "wrong"] += 1
                rec["correct"] = ok
                if not ok:
                    wrong_rows.append({
                        "id": it["id"], "text": text[:140],
                        "value": str(served)[:40],
                        "gold": str(it["gold"])[:30], "path": path})
        else:
            st["escalated"] += 1
            by_k["k%s" % it.get("k")]["escalated"] += 1
        rows.append(rec)
    wall = time.perf_counter() - t0

    n = len(items)
    n_dist = sum(1 for i in items if i.get("distractor"))
    n_in = n - n_dist
    served = st["served"]
    summ = {"arm": a.arm, "split": a.split, "n": n,
            "in_domain": n_in, "distractors": n_dist,
            "served": served, "chain_served": st["chain_served"],
            "plan_served": st["plan_served"],
            "mint_served": st["mint_served"],
            "correct": st["correct"], "WRONG": st["WRONG"],
            "coverage_in_domain": round(served / n_in, 4) if n_in
            else None,
            "wrong_fire": round(st["WRONG"] / served, 6) if served
            else None,
            "SAFETY2_distractor_served": st["SAFETY2_SERVED"],
            "gate_killed": st["gate_killed"],
            "escalated": st["escalated"],
            "engine_errors": st["engine_error"],
            "ms_per_query": round(1000 * wall / n, 3) if n else None,
            "model_calls": 0,
            "by_k": {k: dict(v) for k, v in sorted(by_k.items())}}
    out = HERE / "results" / "v17"
    out.mkdir(parents=True, exist_ok=True)
    tag = ("_%s" % a.tag) if a.tag else ""
    base = "%s_%s%s" % (a.arm, a.split, tag)
    (out / ("%s_summary.json" % base)).write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    (out / ("%s_wrong.json" % base)).write_text(
        json.dumps({"wrong": wrong_rows, "safety2": safety2},
                   indent=1), encoding="utf-8")
    with open(out / ("%s.jsonl" % base), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({k: v for k, v in summ.items()
                      if k != "by_k"}, indent=1))
    print("by_k:", json.dumps(summ["by_k"]))


if __name__ == "__main__":
    main()
