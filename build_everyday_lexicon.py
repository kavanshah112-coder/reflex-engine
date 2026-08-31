# -*- coding: utf-8 -*-
# origin: new for V1.4 -- W3 everyday countable lexicon (bug audit B18)
"""Builds the countable-noun lexicon the engine uses to derive kinds on
real language.

Why this exists: the physics pack's 77 kinds are domain nouns (speed,
moles, voltage). Real word problems count trees, vases, tickets and
daughters, so engine-derived kinds came back UNKNOWN on nearly all real
language and check 8 never fired -- which would have reproduced V1.3's
D5 exactly: a safety mechanism present in the code and idle in practice.

Two constraints shaped how it is built.

  1. It does NOT go into `packs/physics/kinds.json`. That pack feeds
     Tier A, whose 0.000 wrong-fire over 10,160 traps is the baseline
     this whole version is measured against. A Tier B convenience must
     not put that at risk.

  2. It is NOT hand-written. V1.2's capture-hijack lesson is that a
     hand-authored vocabulary extension proposes and the battery
     disposes. So the nouns are harvested from data -- specifically
     from `v13_traffic_pool.json`, which is WORKING data, never a
     sealed evaluation set. No sealed item contributes a single noun.

Method: collect head nouns appearing immediately after a number, keep
those seen at least MIN_FREQ times, drop anything the physics pack
already claims, and drop measure nouns.

The measure stoplist IS hand-authored, and that is stated rather than
buried. Its failure mode is benign in the direction that matters: a
measure noun wrongly admitted as countable makes check 8 abstain on a
legitimately fractional answer, which costs COVERAGE, not correctness.
The spec requires check 8's coverage cost to be measured anyway
(SPEC section 6.1), so the cost of any stoplist error lands in a number
that is already being reported.
"""
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "results" / "v13" / "data" / "v13_traffic_pool.json"
OUT = HERE / "packs" / "everyday"
MIN_FREQ = 3

# Hand-authored. Nouns that follow a number but denote a MEASURE rather
# than a discrete thing, so an answer in them may legitimately be
# fractional.
MEASURE = {
    "hour", "hours", "minute", "minutes", "second", "seconds", "day",
    "days", "week", "weeks", "month", "months", "year", "years",
    "mile", "miles", "kilometer", "kilometers", "km", "meter",
    "meters", "metre", "metres", "foot", "feet", "inch", "inches",
    "yard", "yards", "centimeter", "centimeters", "cm", "mm",
    "pound", "pounds", "kilogram", "kilograms", "kg", "gram", "grams",
    "ounce", "ounces", "ton", "tons", "liter", "liters", "litre",
    "litres", "gallon", "gallons", "quart", "quarts", "pint", "pints",
    "cup", "cups", "dollar", "dollars", "cent", "cents", "euro",
    "euros", "pound_sterling", "degree", "degrees", "percent",
    "percentage", "point", "points", "square", "squares", "acre",
    "acres", "hectare", "hectares", "mph", "kph",
}

STOP = {
    "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for",
    "with", "from", "by", "as", "is", "are", "was", "were", "be",
    "been", "has", "have", "had", "more", "less", "fewer", "than",
    "each", "every", "per", "other", "others", "same", "different",
    "total", "all", "some", "any", "many", "much", "how", "what",
    "that", "this", "these", "those", "there", "then", "when", "if",
    "so", "but", "not", "no", "yes", "he", "she", "it", "they", "we",
    "you", "his", "her", "its", "their", "our", "your", "him", "them",
    "us", "me", "my", "one", "two", "three", "four", "five", "six",
    "seven", "eight", "nine", "ten", "first", "second_ordinal",
    "left", "right", "new", "old", "big", "small", "long", "short",
    "times", "time", "way", "ways", "thing", "things", "part", "parts",
}

NUM_NOUN = re.compile(
    r"\b\d[\d,]*(?:\.\d+)?\s+(?:[a-z]+-)?([a-z]{3,})\b")


def main():
    items = json.loads(SRC.read_text(encoding="utf-8"))
    freq = Counter()
    for it in items:
        for m in NUM_NOUN.finditer((it.get("q") or "").lower()):
            w = m.group(1)
            if w in STOP or w in MEASURE:
                continue
            freq[w] += 1

    # drop anything the physics pack already claims
    kinds = json.loads(
        (HERE / "packs" / "physics" / "kinds.json").read_text(
            encoding="utf-8"))
    claimed = set()
    for name, spec in kinds.items():
        claimed.add(name.replace("_", " "))
        claimed.update(n.lower() for n in (spec.get("nouns") or []))
        claimed.update(a.lower() for a in (spec.get("aliases") or []))
        if spec.get("unit"):
            claimed.add(spec["unit"].lower())

    nouns = sorted(w for w, c in freq.items()
                   if c >= MIN_FREQ and w not in claimed)

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "_provenance": {
            "built_from": "results/v13/data/v13_traffic_pool.json",
            "source_items": len(items),
            "is_sealed_set": False,
            "min_freq": MIN_FREQ,
            "method": "head noun immediately following a number",
            "measure_stoplist": "hand-authored; errors cost coverage, "
                                "not correctness (see module docstring)",
            "maps_to_kind": "count",
            "note": "V1.4 only. NEVER loaded into packs/physics -- that "
                    "pack feeds Tier A and its 0.000 wrong-fire is the "
                    "baseline this version is measured against.",
        },
        "kind": "count",
        "nouns": nouns,
    }
    (OUT / "count_nouns.json").write_text(
        json.dumps(payload, indent=1), encoding="utf-8")
    print("harvested %d distinct number-adjacent nouns (freq>=%d) "
          "from %d NON-SEALED traffic items"
          % (len(nouns), MIN_FREQ, len(items)))
    print("sample:", nouns[:24])
    print("wrote", OUT / "count_nouns.json")


if __name__ == "__main__":
    main()
