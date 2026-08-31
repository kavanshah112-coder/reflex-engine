# -*- coding: utf-8 -*-
# origin: new for V1.4 -- W2 acceptance gate (V1_4_SPEC section 5)
"""Every AMBIGUITY SET entry must abstain on its positive case and
RESOLVE on its negative case.

The negative must resolve, not merely fail to be ambiguous. A gate that
abstains on both is not discriminating -- it is just refusing, and
refusing is free. This test is what stops the ambiguity set from
becoming a coverage tax disguised as a safety feature.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reflex.relations import (AMBIGUITY_SET, AMBIGUOUS, RESOLVED,  # noqa
                              resolve)

# (entry id, positive span, positive ctx, negative span, negative ctx)
CASES = [
    (1, "three times more points than Sara", None,
        "three times as many apples as Ben", None),
    (2, "she had as much again", None,
        "she bought 5 more in all", None),
    (3, "half again as many marbles", None,
        "half of the 12 apples were sold", {"multiplier_base_stated": True}),
    (4, "5 more than the running total", {"comparand_is_derived": True},
        "5 more than Ben", {"comparand_is_derived": False}),
    (5, "the rest were sold", {"candidate_antecedents": 2},
        "the rest were sold", {"candidate_antecedents": 1}),
    (6, "the average score", {"population_stated": False},
        "the average of the 5 scores in all", {"population_stated": True}),
    (7, "each child got some", {"candidate_distributees": 2},
        "each child got some", {"candidate_distributees": 1}),
    (8, "50% more", {"percent_base_stated": False},
        "20% of the 50 apples were sold", {"percent_base_stated": True}),
    (9, "twice as fast", None,
        "twice the 6 apples were bought", {"multiplier_base_stated": True}),
    (10, "how many remain", {"depletion_events": 2},
         "how many were left", {"depletion_events": 1}),
    (11, "between 5 and 10", None,
         "5 and 10 in all", None),
    (12, "up to 5 boxes", None,
         "exactly 5 were sold", None),
    # A13's frozen text names both "above average" and "faster than
    # usual". "above average" is ALSO A6 (an average with no stated
    # population) and A6 is checked first, so the positive here uses
    # A13's distinctive family. The overlap is recorded rather than
    # engineered away: the span abstains either way, which is the
    # property that matters, and narrowing a FROZEN entry to make a
    # test pass would be editing the pre-registration.
    (13, "ran faster than usual", None,
         "scored higher than Ben and Ann in all", None),
    (14, "5 per box", {"candidate_distributees": 2},
         "5 per box", {"candidate_distributees": 1}),
]


def main():
    assert len(CASES) == len(AMBIGUITY_SET), (
        "every frozen ambiguity entry needs a case pair")
    fails = []
    for eid, pos, pctx, neg, nctx in CASES:
        name = [e[1] for e in AMBIGUITY_SET if e[0] == eid][0]
        p = resolve(pos, pctx)
        if p.status != AMBIGUOUS:
            fails.append("A%d %s: POSITIVE %r -> %s (want ambiguous)"
                         % (eid, name, pos, p.status))
        elif not p.rule.startswith("A%d:" % eid):
            fails.append("A%d %s: POSITIVE matched the WRONG entry (%s)"
                         % (eid, name, p.rule))
        n = resolve(neg, nctx)
        if n.status != RESOLVED:
            fails.append("A%d %s: NEGATIVE %r -> %s/%s (want resolved)"
                         % (eid, name, neg, n.status, n.rule or n.why))
        print("  A%-2d %-28s pos=%-9s neg=%s"
              % (eid, name, p.status,
                 "%s(%s)" % (n.status, n.op) if n.op else n.status))

    # documented overlap: A13's other phrasing abstains via A6
    ov = resolve("above average", {"population_stated": False})
    print("  overlap check: 'above average' -> %s (%s)"
          % (ov.status, ov.rule))
    if ov.status != AMBIGUOUS:
        fails.append("'above average' must abstain by some entry")

    # the V1.3 wrong answer this gate exists for
    w1 = resolve("three times more points than Sara")
    if w1.status != AMBIGUOUS:
        fails.append("V1.3 W-1 span must abstain, got %s" % w1.status)
    print("\n  V1.3 W-1 'three times more' -> %s (%s)"
          % (w1.status, w1.rule))

    if fails:
        print("\nRELATION GATE FAILURES:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("\nW2 RELATION GATE PASSES (%d entries, %d case pairs)"
          % (len(AMBIGUITY_SET), len(CASES)))


if __name__ == "__main__":
    main()
