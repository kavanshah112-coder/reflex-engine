# V1.4 bug audit

Same discipline as V1.0-V1.3: every bug logged with when it entered,
what it cost, superseded results preserved, affected measurements
re-run. Nothing silently overwritten.

---

## B17 — single-letter unit aliases match English function words

Found by the first W3 derivation smoke, before any measurement.

`kinds.json` carries unit symbols as aliases, including one-letter ones
(`a` for amperes, `m` for metres, `s` for seconds). The surface matcher
treated every alias as a word, so:

    "16 vases a day"                 -> current   (matched 'a')
    "8 tickets playing whack a mole" -> current   (matched 'a')

The English article became an ampere. This is the same shape as V1.3's
B12 -- a permissive recogniser used where strictness was needed -- and
it would have poisoned every derived kind on real language, which is
exactly the material W3 exists to type.

Fixed: a surface form of <= 2 characters is a UNIT SYMBOL, and matches
only in numeric context (immediately preceded by a number, optionally
spaced). Longer forms keep word-boundary matching.

Caught before it touched a measurement, so nothing is superseded.

---

## B18 — the physics lexicon does not cover real-language nouns

Not a defect, a coverage fact, and it is load-bearing enough to log.

The pack's 77 kinds are domain nouns: speed, moles, voltage,
reaction_yield. Real word problems count trees, vases, people,
daughters, tickets. First smoke:

    "29 trees"            -> UNKNOWN
    "248 vases"           -> UNKNOWN
    "90 people start"     -> UNKNOWN
    "three daughters"     -> UNKNOWN

So engine-derived kinds are UNKNOWN on most real language, and **check
8 skips** -- which would reproduce V1.3's D5 in a new place: a safety
mechanism present in the code and idle in practice.

Two constraints shape the fix. The lexicon must be extended, but:

  1. it must NOT go into `packs/physics/kinds.json`. That pack feeds
     Tier A, whose 0.000 wrong-fire over 10,160 traps is the baseline
     the whole version is measured against. Editing it risks rung F for
     a Tier B convenience.
  2. it must not be invented by me. V1.2's capture-hijack lesson is
     that a hand-written vocabulary extension proposes and the battery
     disposes.

Resolution: a separate V1.4-only lexicon, consulted by `kindderive`
alone and never loaded into the engine pack, **built from the TRAFFIC
POOL** (`v13_traffic_pool.json`) -- which is working data, not a sealed
evaluation set. No sealed item contributes a single noun to it.


---

## B19 — a colliding unit symbol resolved by sort order

Immediately after B17's fix, the next smoke:

    "60 m of rope"  ->  concentration

`m` is claimed by two kinds: metres (length) and molar
(concentration). The matcher iterated a sorted list and returned
whichever came first, so a genuine collision was settled by
lexicographic order and reported as a derived type.

**This is V1.3's B8 in a new layer.** There, supersession ran before
conflict detection and resolved two live contradictory records by
document order, serving 22.92 cavities with a full certificate. Here,
two kinds claim one symbol and the loser is never consulted. Both are
the same mistake: an ordering decision standing in for a conflict
check.

Fixed: surface forms are indexed to the SET of kinds claiming them. A
form claimed by more than one kind returns UNKNOWN with both claimants
named, which is the same rule the provenance layer already applies to
two disagreeing sources -- disagreement abstains, it does not vote.

Recorded because the recurrence is the interesting part: this is the
third time in two versions that an ordering has quietly substituted for
a conflict check. It is worth treating as a standing review question
for any new resolution step, not as three unrelated bugs.


---

## Discipline note — MIN_FREQ was NOT tuned to rescue a known failure

After the everyday lexicon was built at the pre-chosen `MIN_FREQ = 3`,
check 8 caught one of V1.3's two W-4 instances and missed the other:

    "248 vases of flowers" -> count   -> 15.5 ABSTAINS   caught
    "29 trees"             -> UNKNOWN -> 3.222 serves    missed

`trees` did not reach frequency 3 in the traffic pool. Lowering the
threshold to 2 would very likely admit it and would make check 8 look
better against a case whose answer is already known -- **"29 trees" is
a V1.3 SEALED item.**

The threshold stays at 3. It was chosen as a method parameter before
any derivation was measured, and changing it now, having seen which
sealed answer it misses, is tuning on a sealed set however innocuous
the mechanism looks. The lexicon's coverage is a measurement, and
check 8's real-language hit rate is reported at whatever that coverage
turns out to be.

Recorded because this is the cheapest possible moment to get it wrong
and the least likely one to be noticed later.

Related and working as intended: `15.5 dollars` derives UNKNOWN because
`dollars` is on the measure stoplist, so check 8 does not fire on money.
Money is legitimately fractional; a check that abstained on $15.50 would
be a coverage tax with no safety return.
