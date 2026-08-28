# -*- coding: utf-8 -*-
# origin: new for V1.0 — E0 energy bound (V1_PLAN §1: J/query <= 0.61)
"""Metered parity pass over cplx10_sealed (V0.5 protocol: ambient
calibration, cache-cold process, exclusive run). Local model only.

  python meter_run.py
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARC = HERE / "reflex" / "_arc"
BAT = HERE / "battery"
OUT = HERE / "results" / "parity"
sys.path.insert(0, str(ARC))

from parity_run import build_runner, grade      # noqa: E402


def main():
    from v5.energy import PowerMeter
    run_one = build_runner(resolver_on=False)   # cplx10: no ambiguity;
    # resolver never fires on this suite (verified: resolver_used 0)
    items = json.loads((BAT / "cplx10_sealed.json").read_text(
        encoding="utf-8"))
    meter = PowerMeter(tag="v1_cplx10_metered", raw_dir=OUT)
    meter.start()
    try:
        meter.calibrate_ambient(20)
    except Exception as e:
        print("ambient calibration failed:", e)
    rows = []
    try:
        for it in items:
            w = meter.window(it["id"])
            w.__enter__()
            try:
                r = run_one(it)
            finally:
                w.__exit__(None, None, None)
            row = {"query_id": it["id"],
                   "value": r.get("numeric_value"),
                   "correct": grade(r.get("numeric_value"),
                                    it.get("answer")),
                   "t_ms": r.get("t_ms")}
            if w.result:
                row["gpu_j"] = w.result.get("gpu_j")
                row["cpu_j_model"] = w.result.get("cpu_j_model")
            rows.append(row)
    finally:
        meter.stop()
    with open(OUT / "v1_cplx10_metered.jsonl", "w",
              encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, default=str) + "\n")
    j = [(r.get("gpu_j") or 0) + (r.get("cpu_j_model") or 0)
         for r in rows if r.get("gpu_j") is not None]
    acc = sum(r["correct"] for r in rows) / len(rows)
    jq = sum(j) / len(j) if j else None
    print(f"metered: n={len(rows)} acc={acc:.4f} "
          f"J/query={jq:.3f}" if jq is not None else "no meter data")
    bound = 0.61
    ok = jq is not None and jq <= bound and acc == 1.0
    print("ENERGY BOUND:", "PASS" if ok else "FAIL",
          f"(J/query={jq:.3f} <= {bound}, acc={acc:.4f})")
    verdict = json.loads((OUT / "parity_verdict.json").read_text(
        encoding="utf-8"))
    verdict["energy"] = {"n": len(rows), "acc": acc,
                         "j_query": jq, "bound": bound, "ok": ok}
    (OUT / "parity_verdict.json").write_text(
        json.dumps(verdict, indent=1), encoding="utf-8")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
