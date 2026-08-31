# -*- coding: utf-8 -*-
"""W3/W4 unit tests: the plan IR, its five checks, and execution.
The consumption case is gsm0403's failure shape — correct arithmetic
on an incomplete reading — which no V1.2 mechanism could catch."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))

from reflex import planir                                # noqa: E402
from reflex.packs import loader                          # noqa: E402
loader.apply(HERE / "packs" / "physics")
import v10.universe10 as U10                             # noqa: E402

TEXT = ("A machine draws 900 watts and runs 8 hours a day. "
        "Over 30 days, how much energy does it use?")

GOOD = {
    "quantities": [
        {"id": "q1", "value": 900, "unit": "watts", "kind": "power",
         "span": "900 watts"},
        {"id": "q2", "value": 8, "unit": "hours", "kind": "time",
         "span": "8 hours a day"},
        {"id": "q3", "value": 30, "unit": "", "kind": "count",
         "span": "30 days"}],
    "plan": [
        {"op": "mul", "args": ["q1", "q2"], "out": "s1"},
        {"op": "mul", "args": ["s1", "q3"], "out": "s2"}],
    "target": {"kind": "energy", "scope": "total over 30 days"},
    "dismissed": []}

# gsm0403's shape: right arithmetic, incomplete reading (30 unused)
ORPHAN = {
    "quantities": GOOD["quantities"][:2],
    "plan": [{"op": "mul", "args": ["q1", "q2"], "out": "s1"}],
    "target": {"kind": "energy", "scope": "per day"},
    "dismissed": []}

INVENTED = {
    "quantities": [
        {"id": "q1", "value": 900, "unit": "watts", "kind": "power"},
        {"id": "q2", "value": 7200, "unit": "", "kind": "energy"}],
    "plan": [{"op": "mul", "args": ["q1", "q2"], "out": "s1"}],
    "target": {"kind": "energy", "scope": "total"},
    "dismissed": [{"value": 8, "reason": "x"},
                  {"value": 30, "reason": "x"}]}

BAD_DIM = {
    "quantities": [
        {"id": "q1", "value": 900, "unit": "watts", "kind": "power"},
        {"id": "q2", "value": 8, "unit": "hours", "kind": "time"},
        {"id": "q3", "value": 30, "unit": "", "kind": "count"}],
    "plan": [{"op": "add", "args": ["q1", "q2"], "out": "s1"},
             {"op": "mul", "args": ["s1", "q3"], "out": "s2"}],
    "target": {"kind": "energy", "scope": "total"},
    "dismissed": []}


def main():
    K = U10.KINDS10

    ok, why = planir.validate(GOOD)
    assert ok, why
    v, trace = planir.execute(GOOD)
    assert v == 900 * 8 * 30, v
    assert len(trace) == 2
    print(f"  execute: {v:g} over {len(trace)} steps  OK")

    ok, rep = planir.verify(GOOD, GOOD, TEXT, K)
    assert ok, rep
    assert rep["dimensional"]["dimensionally_verifiable"] >= 1
    print(f"  good plan passes all five checks "
          f"({rep['dimensional']['dimensionally_verifiable']}/"
          f"{rep['dimensional']['steps']} steps dimensionally "
          f"verifiable)  OK")

    ok, orphans = planir.check_consumption(ORPHAN, TEXT)
    assert not ok and 30.0 in orphans, orphans
    ok, _ = planir.verify(ORPHAN, ORPHAN, TEXT, K)
    assert not ok
    print("  gsm0403 shape (right maths, 30 left unused): CAUGHT  OK")

    ok, bad = planir.check_roundtrip(INVENTED, TEXT)
    assert not ok and any(b["why"] == "value_not_in_text"
                          for b in bad), bad
    print("  invented value 7200 not in text: CAUGHT  OK")

    ok, det = planir.check_dimensional(BAD_DIM, K)
    assert not ok and det["why"] == "add_sub_dimension_mismatch"
    print("  power + time dimension mismatch: CAUGHT  OK")

    ok, why = planir.agreement(GOOD, ORPHAN)
    assert not ok, why
    ok, why = planir.agreement(GOOD, GOOD)
    assert ok
    print("  agreement: differing parses rejected, identical OK")

    # execution never trusts a model-supplied result field
    sneaky = dict(GOOD)
    sneaky = {**GOOD, "answer": 999999}
    v2, _ = planir.execute(sneaky)
    assert v2 == 900 * 8 * 30, "engine must ignore model 'answer'"
    print("  model-supplied 'answer' field ignored by executor  OK")
    print("PLAN IR TESTS PASS")


if __name__ == "__main__":
    main()
