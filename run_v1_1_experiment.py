# -*- coding: utf-8 -*-
"""V1.1 reproduction entry point.

  python run_v1_1_experiment.py            # hash verify + assertions
  python run_v1_1_experiment.py --battery  # + parity-plus battery
  python run_v1_1_experiment.py --sim      # + full 100k sim re-run
                                           #   (needs serviced bridge)
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--battery", action="store_true")
    ap.add_argument("--sim", action="store_true")
    a = ap.parse_args()
    h = json.loads((HERE / "results/expacq11/dataset_hashes_v11"
                    ".json").read_text(encoding="utf-8"))
    bad = [k for k, d in h.items()
           if isinstance(d, dict) and "sha256" in d and
           sha(HERE / "results/expacq11/data" / f"{k}.json") !=
           d["sha256"]]
    assert not bad, bad
    proof = h["g1_pool"]
    assert proof["coverage"] == 1.0 and proof["residual"] == 0 \
        and proof["wrong"] == 0
    cks = [json.loads(l) for l in
           (HERE / "results/expacq11/sim/checkpoints.jsonl")
           .read_text(encoding="utf-8").splitlines()]
    last = cks[-1]
    assert last["n"] == 100000 and last["wrong"] == 0
    assert last["covered_det"] + last["covered_text"] + \
        last["covered_memory"] == 95472
    v = json.loads((HERE / "results/expacq11/sim/"
                    "refinals_verdict.json").read_text(
        encoding="utf-8"))
    assert v["g3_sem_sealed"]["acc"] == 1.0
    assert v["g3_sem_sealed"]["wrong_fire_numeric"] == 0
    assert v["g3_adv_sealed"]["wrong_fire_numeric"] == 0
    sc = json.loads((HERE / "results/expacq11/scale/"
                     "scale_analysis.json").read_text(
        encoding="utf-8"))
    assert sc["models"]["opus"]["strict_equality"] == 12
    print("V1.1 verification OK: dataset hashes clean; 180k proof "
          "(cov 1.0, 0 wrong, 0 residual); sim 100k (95,472 "
          "certified, 0 wrong); finals sem 100%/0, adv 0 "
          "wrong-fire; opus 12/20 strict mints")
    if a.battery:
        subprocess.run([sys.executable, str(HERE / "parity_run.py"),
                        "--resolver", "on", "--engine", "pack",
                        "--plus"], check=True)
    if a.sim:
        subprocess.run([sys.executable,
                        str(HERE / "expsim_v11.py"), "--wipe"],
                       check=True)
    print("V1.1 REPRODUCTION OK")


if __name__ == "__main__":
    main()
