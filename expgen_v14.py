# -*- coding: utf-8 -*-
# origin: new for V1.4 -- S1 adversarial semantic suite (SPEC section 13)
"""Generates the sealed adversarial suite as CORRECT/CORRUPTED pairs.

Every case is a query text plus TWO relational states over it: one that
faithfully represents the story, and one carrying exactly one seeded
semantic error. That pairing is deliberate and is what makes the suite
able to answer the question V1.3 could not:

    a detector's DETECTION RATE alone is worthless -- a detector that
    fires on everything scores 100%. Only the pair gives the false
    positive rate alongside it, and V1.3's B10 is the precedent:
    non-degeneracy rejected correct plans whose answer happened to
    equal an input, and nobody noticed until somebody counted.

Because both states are constructed, this measures the SUBSTRATE and
the INTEGRITY LAYER without a model in the loop. That is a real
measurement and a bounded one: it says whether the representation can
hold the distinction, not whether a model can produce the
representation. The second question needs the bridge arms and is
reported separately.

Seeded and deterministic. Sealed by hash before any detector is tuned.
"""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE / "results" / "v14" / "data"

NAMES = ["Ana", "Ben", "Cara", "Dev", "Elle", "Femi", "Gus", "Hana",
         "Ivan", "Jo", "Kit", "Lena", "Milo", "Nia", "Omar", "Pia"]
THINGS = ["apples", "marbles", "stickers", "coins", "cards", "books",
          "pencils", "shells", "buttons", "beads", "tickets", "stamps"]
PLACES = ["the shop", "the fair", "school", "the market", "the park"]


def _mk(rng):
    return (rng.choice(NAMES), rng.choice(NAMES), rng.choice(THINGS),
            rng.choice(PLACES))


# ---------------------------------------------------------------------
# Each builder returns (text, correct_state_spec, corrupt_state_spec,
# ask). State specs are plain dicts so the suite can be sealed as JSON
# and rebuilt identically later.
# ---------------------------------------------------------------------

def g_incorrect_grouping(rng):
    """The 90 - (49 - 19) shape: a later event acting on a superseded
    state. Both readings are arithmetically valid."""
    a, b, thing, _ = _mk(rng)
    t0 = rng.randint(40, 99)
    d1 = rng.randint(5, t0 // 2)
    d2 = rng.randint(3, max(4, (t0 - d1) // 2))
    text = ("There were %d %s. %d were taken, then %d more were taken. "
            "How many %s are left?" % (t0, thing, d1, d2, thing))
    n = [{"span": "%d %s" % (t0, thing), "content": t0,
          "identity": "stock", "order": 0},
         {"span": "%d were taken" % d1, "content": None,
          "identity": "stock", "order": 1, "derived_from": ["n1", "r1"]},
         {"span": "then %d more were taken" % d2, "content": None,
          "identity": "stock", "order": 2, "derived_from": ["n2", "r2"]}]
    r_ok = [{"span": "%d were taken" % d1, "args": ["n1"], "order": 1},
            {"span": "then %d more were taken" % d2, "args": ["n2"],
             "order": 2}]
    # corruption: the second event acts on the FIRST event's node
    r_bad = [{"span": "%d were taken" % d1, "args": ["n1"], "order": 1},
             {"span": "then %d more were taken" % d2, "args": ["n1"],
              "order": 2}]
    return text, (n, r_ok), (n, r_bad), {"identity": "stock"}


def g_wrong_temporal_ordering(rng):
    a, _, thing, _ = _mk(rng)
    x, y = rng.randint(10, 60), rng.randint(2, 9)
    text = ("%s had %d %s in the morning and gave away %d in the "
            "afternoon. How many %s remained?" % (a, x, thing, y, thing))
    n_ok = [{"span": "%d %s" % (x, thing), "content": x,
             "identity": "held", "order": 0},
            {"span": "gave away %d" % y, "content": None,
             "identity": "held", "order": 1,
             "derived_from": ["n1", "r1"]}]
    n_bad = [{"span": "%d %s" % (x, thing), "content": x,
              "identity": "held", "order": 1, "derived_from": ["n2"]},
             {"span": "gave away %d" % y, "content": None,
              "identity": "held", "order": 0}]
    r = [{"span": "gave away %d" % y, "args": ["n1"], "order": 1}]
    return text, (n_ok, r), (n_bad, r), {"identity": "held"}


def g_entity_mismatch(rng):
    a, b, thing, _ = _mk(rng)
    if a == b:
        b = NAMES[(NAMES.index(a) + 1) % len(NAMES)]
    x, y = rng.randint(5, 40), rng.randint(5, 40)
    text = ("%s has %d %s. %s has %d %s. How many does %s have?"
            % (a, x, thing, b, y, thing, a))
    n = [{"span": "%s has %d %s" % (a, x, thing), "content": x,
          "identity": a.lower(), "order": 0},
         {"span": "%s has %d %s" % (b, y, thing), "content": y,
          "identity": b.lower(), "order": 1}]
    r_ok = [{"span": "%s has %d %s" % (a, x, thing), "args": ["n1"],
             "order": 0}]
    # corruption: a relation naming only `a` binds BOTH entities
    r_bad = [{"span": "%s has %d %s" % (a, x, thing),
              "args": ["n1", "n2"], "order": 0}]
    return text, (n, r_ok), (n, r_bad), {"identity": a.lower()}


def g_cross_entity_contamination(rng):
    a, b, thing, _ = _mk(rng)
    if a == b:
        b = NAMES[(NAMES.index(a) + 1) % len(NAMES)]
    x, y = rng.randint(5, 40), rng.randint(5, 40)
    text = ("%s collected %d %s and %s collected %d %s. How many did "
            "%s collect?" % (a, x, thing, b, y, thing, a))
    base = [{"span": "%s collected %d %s" % (a, x, thing), "content": x,
             "identity": a.lower(), "order": 0},
            {"span": "%s collected %d %s" % (b, y, thing), "content": y,
             "identity": b.lower(), "order": 1}]
    n_ok = base + [{"span": "%s collected %d %s" % (a, x, thing),
                    "content": None, "identity": a.lower(), "order": 2,
                    "derived_from": ["n1"]}]
    n_bad = base + [{"span": "How many did %s collect" % a,
                     "content": None, "identity": a.lower(), "order": 2,
                     "derived_from": ["n1", "n2"]}]
    r = []
    return text, (n_ok, r), (n_bad, r), {"identity": a.lower()}


def g_wrong_scope(rng):
    a, _, thing, place = _mk(rng)
    x, y = rng.randint(5, 30), rng.randint(5, 30)
    text = ("At %s there were %d %s and at home there were %d %s. How "
            "many were at %s?" % (place, x, thing, y, thing, place))
    n = [{"span": "at %s there were %d %s" % (place, x, thing),
          "content": x, "identity": "stock", "order": 0,
          "context": {"scope": "away"}},
         {"span": "at home there were %d %s" % (y, thing), "content": y,
          "identity": "stock", "order": 1, "context": {"scope": "home"}}]
    r_ok = [{"span": "at %s there were %d %s" % (place, x, thing),
             "args": ["n1"], "order": 0}]
    r_bad = [{"span": "at %s there were %d %s" % (place, x, thing),
              "args": ["n1", "n2"], "order": 0}]
    return text, (n, r_ok), (n, r_bad), {"identity": "stock"}


def g_duplicate_conflicting(rng):
    _, _, thing, _ = _mk(rng)
    x = rng.randint(10, 50)
    text = "There were %d %s on the shelf. How many %s?" % (x, thing, thing)
    n_ok = [{"span": "%d %s" % (x, thing), "content": x,
             "identity": "shelf", "order": 0}]
    n_bad = n_ok + [{"span": "%d %s" % (x, thing), "content": x + 7,
                     "identity": "shelf", "order": 0}]
    return text, (n_ok, []), (n_bad, []), {"identity": "shelf"}


def g_missing_state_transition(rng):
    a, _, thing, _ = _mk(rng)
    x, y = rng.randint(20, 80), rng.randint(3, 15)
    text = ("%s had %d %s and lost %d. How many %s remain?"
            % (a, x, thing, y, thing))
    n_ok = [{"span": "%d %s" % (x, thing), "content": x,
             "identity": "held", "order": 0},
            {"span": "lost %d" % y, "content": None, "identity": "held",
             "order": 1, "derived_from": ["n1", "r1"]}]
    n_bad = [{"span": "%d %s" % (x, thing), "content": x,
              "identity": "held", "order": 0}]
    r = [{"span": "lost %d" % y, "args": ["n1"], "order": 1}]
    return text, (n_ok, r), (n_bad, r), {"identity": "held"}


def g_contradictory_relations(rng):
    a, _, thing, _ = _mk(rng)
    x, y = rng.randint(10, 60), rng.randint(2, 9)
    text = ("%s bought %d %s and sold %d %s. How many %s?"
            % (a, x, thing, y, thing, thing))
    n = [{"span": "bought %d %s" % (x, thing), "content": x,
          "identity": "held", "order": 0},
         {"span": "sold %d %s" % (y, thing), "content": y,
          "identity": "held", "order": 1}]
    r_ok = [{"span": "sold %d %s" % (y, thing), "args": ["n1", "n2"],
             "order": 1}]
    n = n + [{"span": "How many %s" % thing, "content": None,
              "identity": "held", "order": 2,
              "derived_from": ["n1", "r1"]}]
    r_bad = [{"span": "sold %d %s" % (y, thing), "args": ["n1", "n2"],
              "order": 1},
             {"span": "bought %d %s" % (x, thing), "args": ["n1", "n2"],
              "order": 0}]
    return text, (n, r_ok), (n, r_bad), {"identity": "held"}


def g_plan_query_mismatch(rng):
    """V1.3's W-6 shape: a stated quantity takes no part in the answer.
    'Kaleb won 8 and 7 tickets, candy costs 5 each' -> plan adds 8+7
    and stops; the 5 is dismissed with a circular reason."""
    a, _, _, _ = _mk(rng)
    x, y = rng.randint(4, 20), rng.randint(3, 15)
    each = rng.choice([2, 3, 4, 5])
    text = ("%s won %d tickets and %d tickets. A prize costs %d "
            "tickets. How many prizes could %s buy?"
            % (a, x, y, each, a))
    n = [{"span": "%d tickets" % x, "content": x, "identity": "tickets",
          "order": 0},
         {"span": "%d tickets" % y, "content": y, "identity": "tickets",
          "order": 1},
         {"span": "costs %d tickets" % each, "content": each,
          "identity": "price", "order": 2}]
    n_ok = n + [{"span": "How many prizes", "content": None,
                 "identity": "prizes", "order": 3,
                 "derived_from": ["n1", "n2", "n3"]}]
    n_bad = n + [{"span": "%d tickets and %d tickets" % (x, y),
                  "content": None, "identity": "tickets", "order": 3,
                  "derived_from": ["n1", "n2"]}]
    return text, (n_ok, []), (n_bad, []), {"identity": "prizes"}


def g_unresolved_reference(rng):
    a, b, thing, _ = _mk(rng)
    if a == b:
        b = NAMES[(NAMES.index(a) + 1) % len(NAMES)]
    x = rng.randint(10, 40)
    text = ("%s and %s shared %d %s. The other one kept some. How many?"
            % (a, b, x, thing))
    n = [{"span": "%d %s" % (x, thing), "content": x,
          "identity": "pool", "order": 0}]
    r_ok = [{"span": "shared %d %s" % (x, thing), "args": ["n1"],
             "order": 0}]
    r_bad = [{"span": "The other one kept some", "args": ["n1"],
              "order": 1}]
    return text, (n, r_ok), (n, r_bad), {"identity": "pool"}


BUILDERS = [
    ("incorrect_grouping", g_incorrect_grouping),
    ("wrong_temporal_ordering", g_wrong_temporal_ordering),
    ("entity_mismatch", g_entity_mismatch),
    ("cross_entity_contamination", g_cross_entity_contamination),
    ("wrong_scope", g_wrong_scope),
    ("duplicate_conflicting_entities", g_duplicate_conflicting),
    ("missing_state_transition", g_missing_state_transition),
    ("contradictory_relations", g_contradictory_relations),
    ("plan_query_semantic_mismatch", g_plan_query_mismatch),
    ("unresolved_references", g_unresolved_reference),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1404)
    a = ap.parse_args()

    rng = random.Random(a.seed)
    cases = []
    for cls, fn in BUILDERS:
        for i in range(a.per_class):
            text, (n_ok, r_ok), (n_bad, r_bad), ask = fn(rng)
            cases.append({
                "id": "%s_%03d" % (cls, i),
                "seeded_class": cls,
                "text": text,
                "ask": ask,
                "correct": {"nodes": n_ok, "relations": r_ok},
                "corrupt": {"nodes": n_bad, "relations": r_bad},
            })

    OUT.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(cases, indent=1, sort_keys=True)
    (OUT / "s1_adversarial.json").write_text(blob, encoding="utf-8")
    h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    (OUT / "s1_adversarial.sha256").write_text(h, encoding="utf-8")
    print("S1: %d cases across %d classes (%d per class)"
          % (len(cases), len(BUILDERS), a.per_class))
    print("sealed sha256:", h)
    print("wrote", OUT / "s1_adversarial.json")


if __name__ == "__main__":
    main()
