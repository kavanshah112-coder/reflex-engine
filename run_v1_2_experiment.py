# -*- coding: utf-8 -*-
"""V1.2 reproduction: hash verification + headline assertions.
  python run_v1_2_experiment.py            (add --certify for the
  full live safety-case regeneration via certify.py --full)"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--certify", action="store_true")
    a = ap.parse_args()
    h = json.loads((HERE/"results/real/corpus_hashes.json").read_text(encoding="utf-8"))
    bad = [k for k, d in h.items() if isinstance(d, dict) and "sha256" in d
           and sha(HERE/"results/real/data"/f"{k}.json") != d["sha256"]]
    assert not bad, bad
    sw = json.loads((HERE/"results/certification/seed_sweep_ledger.json").read_text(encoding="utf-8"))
    assert sw["total_items"] == 10160 and sw["total_wrong_fire"] == 0
    e = json.loads((HERE/"results/expacq11/energy_evidence.json").read_text(encoding="utf-8"))
    assert e["summary"]["per_query_mean"] < 1.0 and e["summary"]["batch_mean"] < 0.03
    for arm, wtracks in (("sonnet", (1, 0, 0)), ("opus", (1, 1, 0))):
        for name, want in zip(("real_full_sealed","real_units_sealed","real_theory_sealed"), wtracks):
            rows = [json.loads(l) for l in (HERE/f"results/real/loop_{arm}/ms_{name}.jsonl").read_text(encoding="utf-8").splitlines()]
            wrong = sum(1 for r in rows if r["answered"] and not r["correct"])
            assert wrong == want, (arm, name, wrong, want)
            assert wrong / len(rows) <= 0.02
    print("V1.2 verification OK: corpus hashes clean; sweep 10160/65/0; energy bounds; real-language finals as recorded (gate held everywhere)")
    if a.certify:
        subprocess.run([sys.executable, str(HERE/"certify.py"), "--full"], check=True)
    print("V1.2 REPRODUCTION OK")
if __name__ == "__main__":
    main()
