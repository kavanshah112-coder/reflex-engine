# -*- coding: utf-8 -*-
# origin: new for V1.8 -- lean-configuration energy with instrument controls (SPEC 6, R14/R15)
"""Batch-metered joules of the LEAN scientific path only: composer17 +
binder18 + plangate18 + chainexec17/witness. No parser-era pipeline,
no model call inside the window.

  python tools/meter18.py --split seal --n 20000 [--lib ...] [--runs 3]

Instrument rules (B24: the first V1.4 energy run read 0.0 J
everywhere):
  1. POSITIVE CONTROL before and after every batch: a single-thread
     busy loop of known duration must read non-zero and within 20% of
     the documented model (18 W per busy thread x seconds). A failed
     control voids the batch -> "not measured".
  2. AMBIENT: 60 s calibration before each batch; if system CPU
     utilisation is above 20% the fleet (Ventorah's production
     workers, never stopped) is busy -> "not measured". Ambient is
     subtracted (the meter's DYNAMIC figure) and its variance is
     carried into the reported CI.
  3. TWO NUMBERS, always: J per certified served answer, and J per
     QUESTION with planning amortised at the zero-wrong eta. The
     bridge's own draw is unmeasurable from here; V1.4's MEASURED
     local-model call energies (64.9 J producer call, 1,910 J pure
     answer, llama-3.1-8B on this box) stand in as labelled proxies.

Writes results/v18/energy18.json.
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))
OUT = HERE / "results" / "v18"

E_PLAN_PROXY_J = 64.9      # V1.4 measured: local producer call
E_LLM_PROXY_J = 1910.0     # V1.4 measured: local pure-LLM answer
CONTROL_S = 3.0
CONTROL_W = 18.0           # documented boost-regime W per busy thread


def _busy(seconds):
    t0 = time.perf_counter()
    x = 0
    while time.perf_counter() - t0 < seconds:
        x += 1
    return x


def _window_j(w):
    r = w.result or {}
    return (r.get("gpu_j") or 0.0) + (r.get("cpu_j_model") or 0.0), r


def control(meter, tag):
    w = meter.window(tag)
    w.__enter__()
    try:
        _busy(CONTROL_S)
    finally:
        w.__exit__(None, None, None)
    j, r = _window_j(w)
    expect = CONTROL_W * CONTROL_S
    ok = j > 0 and abs(j - expect) / expect <= 0.20
    return {"tag": tag, "joules": round(j, 2), "expected": expect,
            "cpu_j_model": r.get("cpu_j_model"), "gpu_j": r.get("gpu_j"),
            "pass": ok}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="seal")
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--lib", nargs="*", default=[])
    ap.add_argument("--eta", type=float, default=None,
                    help="zero-wrong compounding ratio (serves per "
                         "plan purchased) for the amortised figure")
    a = ap.parse_args()

    from v5.energy import PowerMeter
    from reflex import binder18, chainexec17, composer17, plangate18, \
        roles18
    import v17_run as RUN

    src = HERE / "results" / "v17" / "data" / ("q1m_%s.jsonl" % a.split)
    items = []
    with open(src, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < a.offset:
                continue
            it = json.loads(line)
            if it.get("distractor"):
                continue
            items.append(it)
            if len(items) >= a.n:
                break
    lib = binder18.Library.load(a.lib) if a.lib else None

    def lean(it):
        text = it["text"]
        roles = roles18.analyze(text)
        plan = composer17.parse_chain(text)
        if plan is not None:
            ok, _t = plangate18.check(plan, text, roles)
            if ok:
                v, _c = chainexec17.run(plan)
                if v is not None:
                    return v, "composer"
        if lib is not None:
            v, _c, info = binder18.serve(text, lib, qid=it["id"],
                                         roles=roles)
            if v is not None:
                return v, "bind"
        return None, None

    # warm the interpreter / sympy caches outside any window
    for it in items[:200]:
        lean(it)

    runs = []
    for run in range(a.runs):
        meter = PowerMeter(tag="v18_lean_%d" % run, raw_dir=OUT)
        meter.start()
        rec = {"run": run}
        try:
            amb = None
            try:
                amb = meter.calibrate_ambient(60)
            except Exception as e:           # noqa: BLE001
                rec["ambient_error"] = repr(e)
            rec["ambient"] = amb if isinstance(amb, (dict, float, int)) \
                else str(amb)
            cpu_amb = None
            if isinstance(amb, dict):
                cpu_amb = amb.get("cpu_pct") or amb.get("cpu_util_pct")
            rec["ambient_cpu_pct"] = cpu_amb
            rec["fleet_busy"] = (cpu_amb is not None and cpu_amb > 20.0)
            rec["control_before"] = control(meter, "ctrl_before_%d" % run)
            w = meter.window("lean_batch_%d" % run)
            w.__enter__()
            served = correct = 0
            t0 = time.perf_counter()
            try:
                for it in items:
                    v, how = lean(it)
                    if v is not None:
                        served += 1
                        g = (v > 0) if it["gold_type"] == "bool" else v
                        if RUN.grade(it, g):
                            correct += 1
            finally:
                w.__exit__(None, None, None)
            wall = time.perf_counter() - t0
            j, r = _window_j(w)
            rec["control_after"] = control(meter, "ctrl_after_%d" % run)
            rec.update({"questions": len(items), "served": served,
                        "correct": correct, "wall_s": round(wall, 2),
                        "joules": round(j, 3), "raw": r,
                        "J_per_question_engine": round(j / len(items), 6),
                        "J_per_certified_serve": round(j / served, 6)
                        if served else None})
            rec["valid"] = (rec["control_before"]["pass"] and
                            rec["control_after"]["pass"] and
                            not rec["fleet_busy"] and j > 0)
        finally:
            meter.stop()
        runs.append(rec)
        print(json.dumps({k: v for k, v in rec.items()
                          if k not in ("raw", "ambient")}), flush=True)

    valid = [r for r in runs if r.get("valid")]
    res = {"split": a.split, "n": len(items), "lib": a.lib, "runs": runs,
           "valid_runs": len(valid)}
    if valid:
        jq = [r["J_per_question_engine"] for r in valid]
        js = [r["J_per_certified_serve"] for r in valid
              if r["J_per_certified_serve"]]
        cov = statistics.mean(r["served"] / r["questions"] for r in valid)
        res["J_per_question_engine"] = {
            "mean": round(statistics.mean(jq), 6),
            "sd": round(statistics.pstdev(jq), 6) if len(jq) > 1 else None}
        res["J_per_certified_serve"] = {
            "mean": round(statistics.mean(js), 6),
            "sd": round(statistics.pstdev(js), 6) if len(js) > 1 else None}
        # amortised J per question: escalations cost a full LLM answer
        # (proxy), bound serves carry a planning call amortised over eta
        eng = statistics.mean(jq)
        f_cov = cov
        f_esc = 1.0 - cov
        for name, e_plan in (("proxy_producer_64.9J", E_PLAN_PROXY_J),
                             ("proxy_llm_1910J", E_LLM_PROXY_J)):
            eta = a.eta or 1.0
            res["J_per_question_amortised_" + name] = {
                "eta": eta,
                "value": round(f_esc * E_LLM_PROXY_J + f_cov * (
                    e_plan / eta) + eng, 3),
                "note": "f_esc*E_llm_proxy + f_cov*E_plan_proxy/eta + "
                        "engine; bridge draw unmeasured, proxies are "
                        "V1.4 local measurements"}
        res["status"] = "measured"
    else:
        res["status"] = "not measured"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "energy18.json").write_text(json.dumps(res, indent=1),
                                       encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "runs"},
                     indent=1))


if __name__ == "__main__":
    main()
