# -*- coding: utf-8 -*-
"""P3 unit tests: static gates, apply/revert exactness, probation
state machine (N=3 confirms, 2 resets -> REJECTED), overlay
persistence + fresh-process reproduction."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from reflex.packs import loader                      # noqa: E402
loader.apply(HERE / "packs" / "physics")
from reflex import acquire as AQ                     # noqa: E402


def snap(inj):
    return json.dumps({
        "EN": {k: sorted(v) for k, v in
               inj.W._EXTRA_NOUNS.items()},
        "ADJ": dict(sorted(inj.W._ADJ.items())),
        "IDX": {k: v for k, v in sorted(inj.W._UNIT_IDX.items())},
        "K10": sorted(inj.U10.KINDS10),
        "REG": sorted(inj.SR.REG11),
        "XC": loader.EXTRA_CANONICAL,
    }, sort_keys=True, default=str)


def main():
    tmp = Path(tempfile.mkdtemp())
    store = AQ.CandidateStore(tmp / "cands.jsonl")
    inj = AQ.Injector()

    # ---- static gates
    ok_c = store.add("lexicon_noun",
                     {"kind": "mass", "noun": "payload"}, "MINER")
    bad_kind = store.add("lexicon_noun",
                         {"kind": "nope", "noun": "x"}, "MINER")
    conflict = store.add("lexicon_noun",
                         {"kind": "speed", "noun": "mass"}, "MINER")
    cap_ok = store.add("new_cap",
                       {"name": "test_double_mass",
                        "inputs": ["mass"], "output": "mass",
                        "expr": "mass * 2"}, "MINER")
    cap_dim = store.add("new_cap",
                        {"name": "test_bad_dim",
                         "inputs": ["mass"], "output": "speed",
                         "expr": "mass * 2"}, "MINER")
    cap_free = store.add("new_cap",
                         {"name": "test_free_var",
                          "inputs": ["mass"], "output": "mass",
                          "expr": "mass + rogue"}, "MINER")
    kind_ok = store.add("new_kind",
                        {"name": "test_torque",
                         "dim": [1, 2, -2, 0, 0, 0, 0],
                         "unit": "nm", "nouns": ["torque"],
                         "aliases": ["nm"]}, "MINER")
    for c, want in ((ok_c, True), (bad_kind, False),
                    (conflict, False), (cap_ok, True),
                    (cap_dim, False), (cap_free, False),
                    (kind_ok, True)):
        got, why = AQ.static_gates(c, inj)
        assert got == want, (c["type"], c["payload"], why)
    print("  static gates: 7/7 verdicts correct")

    # ---- apply/revert exactness for every type
    s0 = snap(inj)
    for c in (ok_c, cap_ok, kind_ok,
              store.add("adj_map", {"adj": "ponderous",
                                    "kind": "mass"}, "MINER"),
              store.add("unit_index", {"unit": "slugs",
                                       "kind": "mass"}, "MINER"),
              store.add("conversion",
                        {"concept": "mass", "units": ["slugs"],
                         "op": "mul", "factor": 14.59}, "MINER")):
        undo = inj.apply(c)
        assert snap(inj) != s0, c["type"]
        inj.revert(undo)
        assert snap(inj) == s0, f"revert not exact: {c['type']}"
    print("  apply/revert: 6 types restore state exactly")

    # ---- probation machine
    calls = {"n": 0, "fail_at": {2}}

    def shadow(batch, cand):
        calls["n"] += 1
        return {"wrong": 1 if calls["n"] in calls["fail_at"]
                else 0, "lift": 0}

    g = AQ.Gauntlet(store, inj, shadow)
    g.screen([ok_c])
    assert ok_c["status"] == "PROBATION"
    g.probation_round([])          # confirm 1
    g.probation_round([])          # FAIL -> reset 1, confirms 0
    g.probation_round([])          # confirm 1
    g.probation_round([])          # confirm 2
    assert ok_c["status"] == "PROBATION" and \
        ok_c["confirms"] == 2 and ok_c["resets"] == 1
    g.probation_round([])          # confirm 3 -> ACTIVE
    assert ok_c["status"] == "ACTIVE", (ok_c["status"],
                                        ok_c["confirms"])
    assert "payload" in inj.W._EXTRA_NOUNS.get("mass", []), \
        "ACTIVE candidate must stay applied"
    # a candidate that keeps failing gets REJECTED after 2 resets
    fail_c = store.add("adj_map", {"adj": "hefty", "kind": "mass"},
                       "MINER")
    g.screen([fail_c])
    calls["fail_at"] = set(range(100))
    g.probation_round([])
    g.probation_round([])
    assert fail_c["status"] == "REJECTED", fail_c["status"]
    print("  probation: confirm/reset/ACTIVE/REJECTED transitions ok")

    # ---- overlay persistence + fresh-process reproduction
    pdir = tmp / "packcopy"
    import shutil
    shutil.copytree(HERE / "packs" / "physics", pdir)
    n = g.write_overlay(pdir)
    assert n == 1, n
    code = f'''
import sys, json
sys.path.insert(0, r"{HERE}")
from reflex.packs import loader
loader.apply(r"{pdir}")
import v10.nlpw10 as W
assert "payload" in W._EXTRA_NOUNS.get("mass", []), W._EXTRA_NOUNS.get("mass")
print("OVERLAY OK")
'''
    p = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True)
    assert "OVERLAY OK" in p.stdout, p.stderr[-800:]
    print("  overlay: fresh process reproduces the acquired state")
    print("ACQUIRE UNIT TESTS PASS")


if __name__ == "__main__":
    main()
