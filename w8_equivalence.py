# -*- coding: utf-8 -*-
# origin: new for V1.4 -- W7/W8 reuse safety + semantic equivalence
"""Can the system tell two similar-looking questions apart, and two
differently-worded questions together?

V1.3's plan cache served seven answers and got seven wrong. The
canonical failure, reproduced here as case 1:

    stored    "Mrs. Hilt picked up a book that has 17 pages.
               She read 11 of them..."          sub(count, count)
    traffic   "Janet bought 2 chocolate, 13 vanilla and 2 strawberry
               cupcakes. How many cupcakes?"
    text similarity 0.642 -> bound positionally -> served 11, truth 17

Two short questions about small counts, lexically close, semantically
opposite: one depletes, the other totals. V1.3 matched on surface text
and bound by position, and every check passed because the checks asked
whether the plan was consistent with the text, never whether it
answered the question.

The rule under test:

    similarity != applicability

A stored plan may execute only if the candidate's relational state
satisfies the plan's recorded preconditions. Reported as a CONFUSION
MATRIX over both directions, because passing one direction by
collapsing the other is the obvious degenerate solution:

    DIFFERENT pairs  must be refused   (V1.3's failure)
    EQUIVALENT pairs must be accepted  (or the mechanism is useless)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE / "results" / "v14"


def signature(state):
    """A plan's semantic signature: the multiset of resolved relation
    operators, plus the identities they act on. Deliberately NOT the
    text and NOT the arity -- those are what V1.3 matched on."""
    from reflex import relations as REL
    ops = []
    for r in sorted(state.relations.values(), key=lambda x: x["id"]):
        out = REL.resolve(r.get("span", ""))
        idents = sorted({(state.get(a) or {}).get("identity")
                         for a in r["args"]
                         if state.get(a)} - {None})
        ops.append((out.op or "?" if out.status == "resolved"
                    else out.status, tuple(idents)))
    return tuple(sorted(ops))


def applicable(stored, candidate):
    """-> (ok, why). Reuse requires the same semantic signature."""
    s1, s2 = signature(stored), signature(candidate)
    if s1 != s2:
        return False, {"why": "signature mismatch",
                       "stored": [list(x) for x in s1],
                       "candidate": [list(x) for x in s2]}
    return True, {"why": "signatures agree", "signature": [list(x)
                                                           for x in s1]}


def text_similarity(a, b):
    """V1.3's matcher, for the contrast column."""
    from reflex.frame import cosine, features
    return cosine(features(a), features(b))


PAIRS = [
    # --- structurally similar / semantically DIFFERENT (must refuse)
    {"kind": "different", "name": "V1.3 W-5 (Mrs Hilt / cupcakes)",
     "a": {"text": "Mrs. Hilt picked up a book that has 17 pages. "
                   "She read 11 of them. How many pages are left?",
           "nodes": [{"span": "17 pages", "content": 17,
                      "identity": "pages", "order": 0}],
           "relations": [{"span": "She read 11 of them",
                          "args": ["n1"], "order": 1}]},
     "b": {"text": "For a party Janet bought some cupcakes. She bought "
                   "2 chocolate, 13 vanilla and 2 strawberry. How many "
                   "cupcakes did she buy?",
           "nodes": [{"span": "2 chocolate", "content": 2,
                      "identity": "cupcakes", "order": 0}],
           "relations": [{"span": "She bought 2 chocolate, 13 vanilla "
                                  "and 2 strawberry",
                          "args": ["n1"], "order": 1}]}},
    {"kind": "different", "name": "gave away vs received",
     "a": {"text": "Ana had 20 coins and gave away 6 coins. How many?",
           "nodes": [{"span": "20 coins", "content": 20,
                      "identity": "coins", "order": 0}],
           "relations": [{"span": "gave away 6 coins", "args": ["n1"],
                          "order": 1}]},
     "b": {"text": "Ana had 20 coins and received 6 coins. How many?",
           "nodes": [{"span": "20 coins", "content": 20,
                      "identity": "coins", "order": 0}],
           "relations": [{"span": "received 6 coins", "args": ["n1"],
                          "order": 1}]}},
    {"kind": "different", "name": "shared equally vs bought more",
     "a": {"text": "12 books were divided equally among the shelves.",
           "nodes": [{"span": "12 books", "content": 12,
                      "identity": "books", "order": 0}],
           "relations": [{"span": "divided equally among the shelves",
                          "args": ["n1"], "order": 1}]},
     "b": {"text": "12 books were on the shelf and she bought 4 books.",
           "nodes": [{"span": "12 books", "content": 12,
                      "identity": "books", "order": 0}],
           "relations": [{"span": "she bought 4 books", "args": ["n1"],
                          "order": 1}]}},
    # --- lexically different / semantically EQUIVALENT (must accept)
    {"kind": "equivalent", "name": "sold vs gave away (both deplete)",
     "a": {"text": "There were 30 stamps and 8 were sold.",
           "nodes": [{"span": "30 stamps", "content": 30,
                      "identity": "stock", "order": 0}],
           "relations": [{"span": "8 were sold", "args": ["n1"],
                          "order": 1}]},
     "b": {"text": "There were 30 stamps and 8 were given away.",
           "nodes": [{"span": "30 stamps", "content": 30,
                      "identity": "stock", "order": 0}],
           "relations": [{"span": "8 were gave away", "args": ["n1"],
                          "order": 1}]}},
    {"kind": "equivalent", "name": "bought vs collected (both add)",
     "a": {"text": "Ben had 9 shells and bought 5 shells.",
           "nodes": [{"span": "9 shells", "content": 9,
                      "identity": "stock", "order": 0}],
           "relations": [{"span": "bought 5 shells", "args": ["n1"],
                          "order": 1}]},
     "b": {"text": "Ben had 9 shells and collected 5 shells.",
           "nodes": [{"span": "9 shells", "content": 9,
                      "identity": "stock", "order": 0}],
           "relations": [{"span": "collected 5 shells", "args": ["n1"],
                          "order": 1}]}},
    {"kind": "equivalent", "name": "lost vs used (both deplete)",
     "a": {"text": "Kit had 40 beads and lost 12 beads.",
           "nodes": [{"span": "40 beads", "content": 40,
                      "identity": "stock", "order": 0}],
           "relations": [{"span": "lost 12 beads", "args": ["n1"],
                          "order": 1}]},
     "b": {"text": "Kit had 40 beads and used 12 beads.",
           "nodes": [{"span": "40 beads", "content": 40,
                      "identity": "stock", "order": 0}],
           "relations": [{"span": "used 12 beads", "args": ["n1"],
                          "order": 1}]}},
]


def build(spec):
    from reflex.rss import State
    st = State(spec["text"])
    for n in spec["nodes"]:
        meta = {k: v for k, v in n.items()
                if k not in ("span", "content")}
        st.add_node(n["span"], n.get("content"), **meta)
    for r in spec["relations"]:
        meta = {k: v for k, v in r.items() if k not in ("span", "args")}
        st.add_relation(r["span"], r["args"], **meta)
    return st


def main():
    rows, mat = [], {"different": {"refused": 0, "accepted": 0},
                     "equivalent": {"refused": 0, "accepted": 0}}
    print("%-38s %-11s %6s  %-14s %s"
          % ("pair", "truth", "textsim", "surface-only", "V1.4"))
    for p in PAIRS:
        A, B = build(p["a"]), build(p["b"])
        ok, why = applicable(A, B)
        sim = text_similarity(p["a"]["text"], p["b"]["text"])
        # NOT a reproduction of V1.3's matcher. These pair texts are
        # shortened paraphrases, so their similarity is not comparable
        # to V1.3's recorded score on the original full queries (0.642
        # for the Mrs Hilt / cupcakes pair, which V1.3 DID reuse, and
        # served 11 for a truth of 17). The column is descriptive of
        # THESE texts only and is labelled accordingly.
        v13 = "(would reuse)" if sim >= 0.62 else "(below thr)"
        v14 = "REUSE" if ok else "REFUSE"
        mat[p["kind"]]["accepted" if ok else "refused"] += 1
        rows.append({"name": p["name"], "truth": p["kind"],
                     "text_similarity": round(sim, 3),
                     "v13_would": v13, "v14_does": v14,
                     "why": why})
        print("%-38s %-11s %6.3f  %-14s %s"
              % (p["name"][:38], p["kind"], sim, v13, v14))

    correct = mat["different"]["refused"] + mat["equivalent"]["accepted"]
    total = len(PAIRS)
    print("\n  CONFUSION MATRIX")
    print("    structurally similar / semantically DIFFERENT:"
          "  refused %d / %d" % (mat["different"]["refused"],
                                 sum(mat["different"].values())))
    print("    lexically different / semantically EQUIVALENT:"
          "  accepted %d / %d" % (mat["equivalent"]["accepted"],
                                  sum(mat["equivalent"].values())))
    print("    overall correct: %d / %d" % (correct, total))
    rep = {"matrix": mat, "correct": correct, "n": total, "pairs": rows}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "w8_equivalence.json").write_text(json.dumps(rep, indent=1),
                                             encoding="utf-8")
    print("\nwrote", OUT / "w8_equivalence.json")


if __name__ == "__main__":
    main()
