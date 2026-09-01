# -*- coding: utf-8 -*-
# origin: new for V1.5 -- the brief's section 4 distinction test
"""Four sentences a flat representation cannot tell apart.

Each carries a POSITIVE control (what must be distinguished) beside a
NEGATIVE one (what must NOT be split apart), per the standing
requirement adopted after six instances of a green check that could not
go red. A test that only checks "these four differ" passes trivially if
the indexer emits a unique random signature per input.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "reflex" / "_arc"))

FOUR = [
    ("John has 5 apples.", "possession", None, None, 1),
    ("John gives 5 apples to Sarah.", "transfer", "john", "sarah", 1),
    ("Sarah gives John 5 apples.", "transfer", "sarah", "john", 1),
    ("John had 5 apples before giving Sarah 2 apples.",
     "possession", None, None, 2),
]

# NEGATIVE controls: pairs that MUST share a signature. If paraphrase
# splits them, the indexer is keying on surface text and the four-way
# result above is worthless.
SAME = [
    ("Mary gives 3 pens to Tom.", "Mary gave 3 pens to Tom."),
    ("Ann has 7 coins.", "Ann had 7 coins."),
]


def main():
    from reflex.packs import loader
    loader.apply(Path(__file__).resolve().parents[1] / "packs" /
                 "physics")
    from reflex import packet as PK, packet_index as PI

    fails = []
    sigs = {}
    for q, kind, frm, to, n_rel in FOUR:
        p, _ = PK.build(q)
        st, _ = PI.index(p, q)
        sigs[q] = PI.signature(st)
        rels = sorted(st.relations.values(),
                      key=lambda x: (x.get("order") or 0))
        if len(rels) != n_rel:
            fails.append("%r: %d relations, want %d"
                         % (q, len(rels), n_rel))
            continue
        r0 = rels[0]
        d = r0.get("direction") or {}
        if r0.get("relation_kind") != kind:
            fails.append("%r: first relation %s, want %s"
                         % (q, r0.get("relation_kind"), kind))
        if d.get("from") != frm or d.get("to") != to:
            fails.append("%r: direction %s->%s, want %s->%s"
                         % (q, d.get("from"), d.get("to"), frm, to))
        print("  %-48s %s" % (q, [(r.get("relation_kind"),
                                   (r.get("direction") or {}).get("from"),
                                   (r.get("direction") or {}).get("to"))
                                  for r in rels]))

    if len({v for v in sigs.values()}) != 4:
        fails.append("the four cases must have four distinct signatures")

    # the decisive pair: same tokens, opposite meaning
    a = sigs["John gives 5 apples to Sarah."]
    b = sigs["Sarah gives John 5 apples."]
    if a == b:
        fails.append("prepositional and ditransitive must differ")

    print()
    for x, y in SAME:
        px, _ = PK.build(x)
        py, _ = PK.build(y)
        sx = PI.signature(PI.index(px, x)[0])
        sy = PI.signature(PI.index(py, y)[0])
        ok = sx == sy
        print("  %-34s == %-34s %s" % (x, y, "same" if ok else "SPLIT"))
        if not ok:
            fails.append("paraphrase split: %r vs %r" % (x, y))

    if fails:
        print("\nPACKET INDEX FAILURES:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("\nPACKET INDEX TESTS PASS "
          "(4 distinguished, %d paraphrase pairs held together)"
          % len(SAME))


if __name__ == "__main__":
    main()
