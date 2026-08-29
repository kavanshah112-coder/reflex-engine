# -*- coding: utf-8 -*-
# origin: new for V1.2 — W3 energy evidence pack (V1_2_SPEC)
"""Energy measurement, two instruments, three runs each (exclusive):

  python meter_v12.py

A) per-query windows (V0.5 protocol-compatible): 500 g2 items — the
   arc's historical instrument; at sub-ms/query the reading is
   window-overhead-dominated (documented).
B) batch windows: one window around 5,000 queries (~5 s of compute),
   well above the meter's 200 ms sampling resolution — the accurate
   instrument for sub-ms work.
Plus one cold-start measurement (first query of a fresh process is
timed separately in run 1 of A).
Writes results/expacq11/energy_evidence.json.
"""
import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
OUT = HERE / "results" / "expacq11"


def main():
    from v5.energy import PowerMeter
    from reflex.engine import Engine
    items = json.loads((OUT / "data" / "g2_commercial.json")
                       .read_text(encoding="utf-8"))
    ev = {"per_query_runs": [], "batch_runs": [],
          "cold_start_ms": None}
    eng = Engine()
    t0 = time.perf_counter()
    eng.run_query(items[0]["q"], "cold")
    ev["cold_start_ms"] = round((time.perf_counter() - t0) * 1e3, 1)

    for run in range(3):
        meter = PowerMeter(tag=f"v12_pq_{run}", raw_dir=OUT)
        meter.start()
        try:
            meter.calibrate_ambient(20)
        except Exception as e:
            print("ambient failed:", e)
        js = []
        try:
            for it in items[:500]:
                w = meter.window(it["id"])
                w.__enter__()
                try:
                    eng.run_query(it["q"], f"pq{run}_{it['id']}")
                finally:
                    w.__exit__(None, None, None)
                if w.result and w.result.get("gpu_j") is not None:
                    js.append((w.result.get("gpu_j") or 0) +
                              (w.result.get("cpu_j_model") or 0))
        finally:
            meter.stop()
        jq = sum(js) / len(js) if js else None
        ev["per_query_runs"].append({"n": len(js), "j_query": jq})
        print(f"per-query run {run}: J/q={jq:.3f}", flush=True)

    for run in range(3):
        meter = PowerMeter(tag=f"v12_batch_{run}", raw_dir=OUT)
        meter.start()
        try:
            meter.calibrate_ambient(20)
        except Exception as e:
            print("ambient failed:", e)
        try:
            w = meter.window(f"batch{run}")
            w.__enter__()
            try:
                for it in items[1000:6000]:
                    eng.run_query(it["q"], f"b{run}_{it['id']}")
            finally:
                w.__exit__(None, None, None)
        finally:
            meter.stop()
        if w.result and w.result.get("gpu_j") is not None:
            tot = (w.result.get("gpu_j") or 0) + \
                (w.result.get("cpu_j_model") or 0)
            ev["batch_runs"].append({"n": 5000, "j_total": tot,
                                     "j_query": tot / 5000})
            print(f"batch run {run}: J/q={tot/5000:.4f}",
                  flush=True)

    pq = [r["j_query"] for r in ev["per_query_runs"]
          if r["j_query"]]
    bt = [r["j_query"] for r in ev["batch_runs"]]
    ev["summary"] = {
        "per_query_mean": statistics.mean(pq) if pq else None,
        "per_query_stdev": statistics.stdev(pq) if len(pq) > 1
        else None,
        "batch_mean": statistics.mean(bt) if bt else None,
        "batch_stdev": statistics.stdev(bt) if len(bt) > 1
        else None,
        "method_note": "per-query windows are overhead-dominated at "
                       "sub-ms/query (200 ms sampling); the batch "
                       "instrument is authoritative for the "
                       "certified-serve cost"}
    (OUT / "energy_evidence.json").write_text(
        json.dumps(ev, indent=1), encoding="utf-8")
    print("summary:", json.dumps(ev["summary"]))


if __name__ == "__main__":
    main()
