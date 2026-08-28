# -*- coding: utf-8 -*-
"""V1.0 reproduction entry point (V1_SPEC §0.6).

  python run_v1_0_experiment.py                # verify + analysis
  python run_v1_0_experiment.py --parity       # + re-run the parity
                                               #   battery live (needs
                                               #   ollama for resolver)
  python run_v1_0_experiment.py --arm A0       # re-run one arm live

Default mode is hash-gated verification + deterministic re-analysis:
checks every sealed dataset and vendored-module hash, then rebuilds
results/expacq/analysis.json from the recorded arm outputs and
asserts the headline numbers. Arm re-runs are deterministic for
A0/A1; mining arms depend on live model outputs and are recorded
evidence (their stores and logs are committed).
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


def verify_hashes():
    bad = []
    h = json.loads((HERE / "results/expacq/dataset_hashes.json")
                   .read_text(encoding="utf-8"))
    for name, d in h.items():
        if not isinstance(d, dict) or "sha256" not in d:
            continue
        p = HERE / "results/expacq/data" / f"{name}.json"
        if sha(p) != d["sha256"]:
            bad.append(name)
    o = json.loads((HERE / "reflex/_arc/ORIGINS.json")
                   .read_text(encoding="utf-8"))
    for rel, d in o.items():
        p = (HERE / "reflex/_arc" / rel if not
             rel.startswith(("battery/", "data/")) else HERE / rel)
        if p.exists() and sha(p) != d["sha256"]:
            bad.append(rel)
    print(f"hash verification: {len(h) - 2 + len(o)} files, "
          f"{len(bad)} mismatches")
    assert not bad, bad


def analysis():
    subprocess.run([sys.executable,
                    str(HERE / "expanalyze_v1.py")], check=True)
    a = json.loads((HERE / "results/expacq/analysis.json")
                   .read_text(encoding="utf-8"))
    ps = {arm: a["arms"][arm]["expacq_parse_sealed"]
          for arm in a["arms"] if
          a["arms"][arm].get("expacq_parse_sealed")}
    assert ps["A0"]["acc"] == 0.0 and ps["A2"]["acc"] == 0.0
    assert abs(ps["A2-haiku"]["acc"] - 0.058) < 1e-9
    assert abs(ps["A2-sonnet"]["acc"] - 0.072) < 1e-9
    assert all(v["gate_rate"] == 0.0 for v in ps.values())
    print("headline assertions hold: A0/A2 0.0, haiku 5.8%, "
          "sonnet 7.2%, gate 0.000 everywhere")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parity", action="store_true")
    ap.add_argument("--arm", default=None)
    a = ap.parse_args()
    verify_hashes()
    analysis()
    if a.parity:
        subprocess.run([sys.executable, str(HERE / "parity_run.py"),
                        "--resolver", "on", "--engine", "pack"],
                       check=True)
    if a.arm:
        subprocess.run([sys.executable, str(HERE / "exparms_v1.py"),
                        "--arm", a.arm], check=True)
    print("V1.0 REPRODUCTION OK")


if __name__ == "__main__":
    main()
