# -*- coding: utf-8 -*-
# origin: new for V1.1 — metered engine sample (V1_1_SPEC §5)
"""Exclusive metered sample: 500 g2-commercial items through the
W1c engine (V0.5 protocol). Yields the engine-side J/query applied
to the commercial cost model in analysis."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
OUT = HERE / "results" / "expacq11"


def main():
    from v5.energy import PowerMeter
    from reflex.engine import Engine
    eng = Engine()
    items = json.loads((OUT / "data" / "g2_commercial.json")
                       .read_text(encoding="utf-8"))[:500]
    meter = PowerMeter(tag="v11_engine_sample", raw_dir=OUT)
    meter.start()
    try:
        meter.calibrate_ambient(20)
    except Exception as e:
        print("ambient calibration failed:", e)
    js = []
    try:
        for it in items:
            w = meter.window(it["id"])
            w.__enter__()
            try:
                eng.run_query(it["q"], f"me_{it['id']}")
            finally:
                w.__exit__(None, None, None)
            if w.result and w.result.get("gpu_j") is not None:
                js.append((w.result.get("gpu_j") or 0) +
                          (w.result.get("cpu_j_model") or 0))
    finally:
        meter.stop()
    jq = sum(js) / len(js) if js else None
    (OUT / "engine_energy_sample.json").write_text(json.dumps(
        {"n": len(js), "j_query": jq}, indent=1), encoding="utf-8")
    print(f"engine sample: n={len(js)} J/query={jq:.3f}")


if __name__ == "__main__":
    main()
