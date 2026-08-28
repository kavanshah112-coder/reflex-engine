# -*- coding: utf-8 -*-
"""Automatic invariant tests I1-I8 (spec Section 22). Run:
    python v11/test_invariants11.py
Constructs adversarial states directly and asserts the machine-
checkable invariants hold through certify + run."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v11.semstate11 import SemanticState            # noqa: E402
from v11.integrity11 import certify, check_invariants  # noqa: E402
from v11.semrun11 import run                        # noqa: E402

PASS = []


def check(name, cond):
    PASS.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), name)


def s():
    return SemanticState()


# I1: no conflicted fact enters certified state
st = s()
st.add(entity="GLOBAL", concept="mass", value=20, unit="kg",
       span="20 kg")
st.add(entity="GLOBAL", concept="mass", value=15, unit="kg",
       span="15 kg")
certify(st)
check("I1_conflict_not_certified",
      all(f["status"] == "CONFLICTED" for f in st.facts))
check("I1_invariant_clean", not check_invariants(st))

# I2: ambiguous entity cannot satisfy an entity-specific requirement
st = s()
e1 = st.graph.add("Tank A")
e2 = st.graph.add("Tank B")
f = st.add(entity=None, concept="solution_volume", value=500,
           unit="l", span="500 L")
f["ambiguity"] = [e1, e2]
certify(st)
check("I2_ambiguous_blocked", f["status"] == "AMBIGUOUS")
viol = check_invariants(st, executed_inputs=[f], target_entity=e1)
check("I2_consumption_flagged", any(v[0].startswith("I2")
                                    for v in viol))

# I3: cross-entity consumption flagged
st = s()
e1 = st.graph.add("Car A")
e2 = st.graph.add("Car B")
fa = st.add(entity=e1, concept="mass", value=100, unit="kg",
            span="100 kg")
certify(st)
viol = check_invariants(st, executed_inputs=[fa], target_entity=e2)
check("I3_cross_entity_flagged", any(v[0] == "I3" for v in viol))

# I4: LLM output cannot directly overwrite certified state — the
# resolver path only fills AMBIGUOUS facts and only via validation
st = s()
e1 = st.graph.add("Silo A")
e2 = st.graph.add("Vat B")
f1 = st.add(entity=e1, concept="mass", value=25, unit="kg",
            span="25 kg")
certify(st)


def bad_resolver(q, fact, state):
    return e1     # tries to bind onto an entity that HAS the concept


f2 = st.add(entity=None, concept="mass", value=99, unit="kg",
            span="99 kg")
f2["ambiguity"] = [e1, e2]
f2["status"] = "AMBIGUOUS"
r = run(st, {"target_concept": "energy", "target_entity": e1,
             "target_candidates": []},
        "Silo A holds 25 kg. 99 kg. energy?", "t4",
        resolver=bad_resolver)
check("I4_wrong_llm_proposal_rejected", f2["status"] == "AMBIGUOUS")

# I5: derived values need provenance
st = s()
d = st.add(entity="GLOBAL", concept="energy", value=100,
           provenance="DERIVED", span="")
certify(st)
check("I5_derived_without_source_blocked",
      d["status"] == "QUARANTINED")

# I7/I8: failed integrity cannot fall through; quarantined state not
# consumed by dependents
st = s()
a = st.add(entity="GLOBAL", concept="mass", value=20, unit="kg",
           span="20 kg")
b = st.add(entity="GLOBAL", concept="mass", value=30, unit="kg",
           span="30 kg")
c = st.add(entity="GLOBAL", concept="energy", value=999,
           provenance="DERIVED", derived_from=[a["fid"]],
           span="")
certify(st)
check("I8_dependent_quarantined", c["status"] == "QUARANTINED")

n_fail = sum(1 for _, ok in PASS if not ok)
print(f"\n{len(PASS) - n_fail}/{len(PASS)} invariant tests pass")
sys.exit(1 if n_fail else 0)
