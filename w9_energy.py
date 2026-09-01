# -*- coding: utf-8 -*-
# origin: new for V1.4 -- H9 end-to-end energy (SPEC section 16)
"""Measures joules per query and per CORRECT answer, end to end.

V1.3 made no energy claim at all. Its bridge token counts turned out to
be fabricated -- one servicing agent reverse-engineered an earlier
agent's invented formula and reproduced it faithfully, so the fiction
grew more convincing as it spread (B7). This run exists to replace that
hole with a measurement, and it can only be done locally, because the
bridge runs on someone else's hardware and reports nothing real.

THE ACCOUNTING BOUNDARY IS THE CLAIM. Every model call is inside it,
including the state producer. V1.2's headline figure -- 21 mJ per
certified serve -- measured the ENGINE only, with the model's own work
outside the window; that number is true and answers a different
question than the one a buyer asks. Here the window wraps the whole
pipeline: producer call, span verification, kind derivation, relation
resolution, integrity, execution.

Two arms on the same items, same hardware, same meter:

  REFLEX   producer -> substrate -> gates -> certified or abstained
  PURE LLM the same local model asked for the answer directly

Reported for both: J/query, J/correct, and the reflex arm's split
across pipeline stages. Correctness is graded against the sealed
answers, so J/correct counts abstentions as spend with no return --
which is the honest denominator for a system whose whole design is to
decline.
"""
import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
DATA = HERE / "results" / "v14" / "data"
OUT = HERE / "results" / "v14"

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
DIRECT = ("Solve this problem. Reply with ONLY the final number, no "
          "words, no units.\n\nPROBLEM: {q}")


def grade(v, a, tol=2e-2):
    if v is None or a is None:
        return False
    try:
        v, a = float(v), float(a)
    except (TypeError, ValueError):
        return False
    return abs(v) < 1e-9 if a == 0 else abs(v - a) / abs(a) <= tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=60)
    ap.add_argument("--model", default="llama3.1:8b")
    ap.add_argument("--split", default="s3_real_language")
    a = ap.parse_args()

    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    from reflex.adapters.ollama import OllamaAdapter
    from reflex import state_agent as SA
    from v5.energy import PowerMeter
    from w2_v14 import ARMS, solve

    items = json.loads((DATA / ("%s.json" % a.split))
                       .read_text(encoding="utf-8"))[:a.n]
    adapter = OllamaAdapter(model=a.model)
    cfg = ARMS["C5"]

    meter = PowerMeter(tag="v14_energy")
    meter.start()
    try:
        if hasattr(meter, "calibrate"):
            try:
                meter.calibrate()
            except Exception:
                pass

        # ---------------- arm 1: the reflex pipeline ----------------
        st = Counter()
        rows, e_reflex = [], []
        for it in items:
            t0 = time.time()
            with meter.window("reflex_%s" % it["id"]) as w:
                r = solve(adapter, it, cfg)
            st[r["status"]] += 1
            if r["status"] == "certified":
                st["correct" if r.get("correct") else "WRONG"] += 1
            e = dict(w) if isinstance(w, dict) else {}
            e_reflex.append(e)
            rows.append({"id": it["id"], "status": r["status"],
                         "correct": bool(r.get("correct")),
                         "wall_s": round(time.time() - t0, 2),
                         "energy": e})

        # ---------------- arm 2: pure LLM, same items ---------------
        pure_ok = 0
        e_pure = []
        for it in items:
            with meter.window("pure_%s" % it["id"]) as w:
                try:
                    c = adapter.complete(DIRECT.format(q=it["q"]),
                                         max_tokens=24)
                    m = NUM.findall((c.text or "").replace(",", ""))
                    v = float(m[-1]) if m else None
                except Exception:
                    v = None
            if grade(v, it.get("answer")):
                pure_ok += 1
            e_pure.append(dict(w) if isinstance(w, dict) else {})
    finally:
        meter.stop()

    def total(es, key):
        return sum(float(e.get(key) or 0.0) for e in es)

    n = len(items)
    rc = st["correct"]
    rep = {"n": n, "model": a.model, "meter": "v5.energy PowerMeter",
           "boundary": "ALL model calls inside, producer included",
           "levels": {"gpu_j": "LEVEL 2 measured telemetry",
                      "cpu_j_model": "LEVEL 3 documented power model"},
           "reflex": {"status": dict(st), "certified": st["certified"],
                      "correct": rc, "wrong": st["WRONG"]},
           "pure_llm": {"correct": pure_ok}}

    for key in ("gpu_j", "cpu_j_model", "cpu_j_util"):
        r_j, p_j = total(e_reflex, key), total(e_pure, key)
        rep.setdefault("energy", {})[key] = {
            "reflex_total_j": round(r_j, 3),
            "reflex_j_per_query": round(r_j / n, 4) if n else None,
            "reflex_j_per_correct": (round(r_j / rc, 4) if rc else None),
            "pure_total_j": round(p_j, 3),
            "pure_j_per_query": round(p_j / n, 4) if n else None,
            "pure_j_per_correct": (round(p_j / pure_ok, 4)
                                   if pure_ok else None),
        }
    rep["reflex_wall_s"] = round(sum(r["wall_s"] for r in rows), 1)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "w9_energy.json").write_text(json.dumps(rep, indent=1),
                                        encoding="utf-8")
    with open(OUT / "w9_energy_rows.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
