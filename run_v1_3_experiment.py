# -*- coding: utf-8 -*-
# origin: new for V1.3 -- single-command reproduction (SPEC section 14)
"""Reproduces every V1.3 number that can be reproduced offline.

  python run_v1_3_experiment.py            # offline stages + report
  python run_v1_3_experiment.py --list     # show stages, run nothing

WHAT REPRODUCES EXACTLY, with no network and no model:
  W0 recurrence, W1 frame index, the two W6 corpora, W6 R3 (provenance
  certification on both corpora), W5 plan reflexes, Tier A
  certification, and the aggregate table.

WHAT DOES NOT, and why it is not pretended otherwise: the W2 parse
arms and the W6 R1/R2 arms need a model. In V1.3 those ran through
the deferred-replay bridge against a subscription, not an API key, so
they cannot be re-executed by a script. Their RESPONSES are frozen in
`results/bridge_v13/<model>/resp_*.json` and the arms replay from that
cache byte-for-byte -- re-running `w2_bridge.py` against the committed
cache reproduces the published arm numbers without a single new call.
That is reproduction of the measurement, not of the model, and the
distinction is stated rather than blurred.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

STAGES = [
    ("W0  structural recurrence (L1)", ["w0_recurrence.py"]),
    ("W1  frame index + calibration (L2)", ["w1_frame.py"]),
    ("W6  build both corpora", ["corpusgen_v13.py"]),
    ("W6  R3 provenance, generic (L8)",
     ["w6_rag.py", "--corpus", "generic", "--arm", "r3"]),
    ("W6  R3 provenance, user (L8/L11)",
     ["w6_rag.py", "--corpus", "user", "--arm", "r3"]),
    ("W5  plan reflexes, repeat traffic (L5)",
     ["w5_plancache.py", "--mode", "repeat"]),
    ("W5  plan reflexes, unique traffic (L5)",
     ["w5_plancache.py", "--mode", "unique"]),
    ("W2  replay haiku arm from frozen cache",
     ["w2_bridge.py", "--model", "claude-haiku-4-5",
      "--split", "arm_sample", "--seal"]),
    ("W2  replay sonnet arm from frozen cache",
     ["w2_bridge.py", "--model", "claude-sonnet-5",
      "--split", "arm_sample", "--seal"]),
    ("W2  replay opus arm from frozen cache (EXCLUDED, B9)",
     ["w2_bridge.py", "--model", "claude-opus-5",
      "--split", "arm_sample", "--seal"]),
    ("W7  Tier A + two-tier certificate (L9)", ["certify.py"]),
    ("     aggregate results table", ["expanalyze_v13.py"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for name, cmd in STAGES:
            print("  %-46s python %s" % (name, " ".join(cmd)))
        return
    t0 = time.time()
    results = []
    for name, cmd in STAGES:
        print("\n=== %s ===" % name, flush=True)
        r = subprocess.run([sys.executable] + cmd, cwd=HERE)
        results.append({"stage": name, "rc": r.returncode})
        print("    rc=%d" % r.returncode)
    (HERE / "results" / "v13" / "reproduction.json").write_text(
        json.dumps({"stages": results,
                    "wall_s": round(time.time() - t0)}, indent=1),
        encoding="utf-8")
    bad = [r for r in results if r["rc"] not in (0, 3)]
    print("\n%d/%d stages clean (rc 3 = arm sealed with unresolved "
          "items, expected)" % (len(results) - len(bad), len(results)))
    for r in bad:
        print("  FAILED:", r["stage"])
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
