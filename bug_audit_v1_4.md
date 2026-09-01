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


---

## B20 — a shell-mangled escape produced a detector that matched nothing

While narrowing the integrity detectors, a patch applied through a
shell heredoc turned every  into a literal BACKSPACE character
(0x08). The referential-reference detector compiled to

    re.compile(chr(8) + "(it|they|the other|...)" + chr(8))

which is a valid regex that matches a control character, so it matched
nothing, raised nothing, and reported a clean result on every state.
Detection for that class read 0% and looked like a modelling failure.

The bug is mundane; its SHAPE is the one this arc keeps meeting. A
check that is present in the code, runs without error, and is
structurally incapable of firing:

    V1.3 B16  consumption went silent on all-word problems
    V1.3 B8   supersession starved the conflict check of its input
    V1.4 B19  a colliding surface resolved by sort order
    V1.4 B20  a mangled escape produced an inert regex

Four instances in two versions of the same failure mode -- a green
check that cannot go red. The fix here was mechanical (repair the
escape). The lesson is not: **a detector reporting zero findings needs
a positive control before it is believed.** The dev/sealed split caught
this one only because a class that should have detected 100% reported
0% and was worth chasing. A class with a plausible-looking 60% would
have shipped.

Recorded as a standing test requirement for V1.4: every detector needs
a case it MUST fire on, and that case runs in CI alongside the case it
must not fire on.


---

## Finding — agreement failures on the substrate are structural, and a
## correction to how I first read them

On the haiku C5 arm, agreement became the dominant abstention: 20 of 27
resolved items. Before accepting that, the same question V1.3's D7
asked was asked here -- is the check rejecting equivalent readings over
naming?

The first decomposition said yes for 5 of 27: identity labels differed
while operators matched (`pigeons`/`pigeon`,
`seeds_per_watermelon`/`quantity`). Labels are free text a producer
chooses, so excluding them from the signature looked clearly right.

**Excluding them recovered nothing.** Failures went 19 -> 20.

The decomposition was wrong. It compared FLATTENED identity lists, so a
sample that split a story into MORE relations appeared as a naming
difference:

    A = [seeds_per_watermelon, watermelons]     2 relations
    B = [quantity, quantity, seeds, seeds]      4 relations

That is a structural disagreement about how many events the story
contains, wearing the costume of a vocabulary disagreement.

The signature keeps labels excluded -- that remains right on principle,
since two samples agreeing on spelling is not what the check is for --
but the number does not improve, and the conclusion inverts: **two
samples of one model produce structurally different relational states
for the same problem in roughly three quarters of resolved cases.**

Recorded because the wrong reading was the more comfortable one. It
would have turned a hard finding about producer instability into a
tidy story about a fixable comparison bug, and the only thing that
caught it was that the fix did not work.


---

## B22 — the substrate executor shipped without non-degeneracy

The C1 arm served 8 answers on sealed real language and every one was
wrong. Not 8 different mistakes -- one mistake, 8 times:

    "I see 349 frogs. How many legs do they have?"        served 349
    "18 cubes long ... it doubles her length"             served 18
    "Mrs. Hilt read 2 books per day ... in one week"      served 2
    "349 frogs" -> 1 node, 0 relations -> terminal IS the given

With no relation resolved, the state has one node, that node is the
only terminal, and the executor returned its content. The answer was
the question's own input, restated.

**V1.3 caught this class.** `check_nondegenerate` (its check 6, added
as V1.3's B4) rejects a plan whose answer equals one of its inputs.
Replacing the representation dropped the guard with it: I re-derived
the substrate and did not re-derive what the old representation was
protecting against.

That is the general hazard of a rewrite, and it is worth stating
plainly because the rewrite was the whole point of this version: **a
new representation inherits none of the old one's scar tissue.** Every
guard the previous design accumulated has to be re-argued in the new
terms, and the ones that are missed are exactly the ones nobody
remembers needing.

Fixed: a terminal with no `derived_from` abstains. Justified by the
mechanism -- a terminal nothing derives is a restated input whatever
the gold answer happens to be -- not by the sealed answers that
revealed it.

Preserve-supersede-rerun applied. Pre-fix arms kept verbatim in
`results/v14/arms/superseded_pre_B22/`. Both readings stand:

    PRE-FIX   C1  8 served / 8 wrong / wrong-fire 1.000
              C2  1 served / 1 wrong / wrong-fire 1.000
              C3  8 served / 8 wrong / wrong-fire 1.000
              C5  0 served
    POST-FIX  every arm 0 served, 0 wrong
