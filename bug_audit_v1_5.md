# V1.5 bug audit

Same discipline as V0.1-V1.4: every bug logged with when it entered and
what it cost, superseded results preserved, affected measurements
re-run, nothing silently overwritten.

---

## B25 — the concept namer fabricates physics kinds on real language

Found while measuring packet completeness, BEFORE any sealed
evaluation.

`nlpw10.name_concept` resolves a quantity's concept through the frozen
V0.9 machinery: noun-phrase match, then token vote, then dimension.
On the generator universe every quantity has a matching noun, so the
fallbacks rarely fire. On real language almost nothing matches, the
fallbacks fire constantly, and they return a CONFIDENT WRONG KIND
instead of UNKNOWN:

    "29 inches of snow"                  -> payback_months
    "105 parents ... 698 pupils"         -> payback_months (both)
    "three touchdowns worth 7 points"    -> z_score (both)
    "$5.00 ... costs $4.28"              -> ad_spend, fixed_cost
    "distance from desk to fountain"     -> fixed_cost, target=time

Most-assigned concept across 400 sealed real-language queries:
**`payback_months`, 131 times.** It is a business-metrics kind. It is
being applied to snow depth, schoolchildren and touchdowns.

**What this does to the version's headline number.** Packet
completeness measured 8.2% by a loose check and 5.0% once conflicts
were separated. Neither figure is usable: the packets are complete in
FORM and meaningless in CONTENT. Real deterministic coverage on real
language is effectively **zero**, and it was never 8.2%.

**Why it is worse than a coverage miss.** A quantity named UNKNOWN
abstains. A quantity named `payback_months` is EXECUTABLE -- it has a
dimension, so the dimensional gate engages and passes, and the answer
carries a certificate. This is V1.3's D5 (vacuous count/money labels)
in its most damaging form: not a label carrying no information, but a
label carrying WRONG information that downstream machinery trusts.

It also explains V1.4's false conflicts. Two unrelated quantities named
the same wrong kind look like one entity holding two values, so the
conflict detector fires on "105 parents / 698 pupils". Roughly one in
eight real-language packets was flagged CONFLICTING for this reason.

**Fix (pre-sealed, legitimate engineering):** naming must be
EVIDENCE-BACKED or UNKNOWN. V1.4 already built exactly that in
`reflex/kindderive.py` -- it requires a real noun, alias or unit match,
abstains on colliding surfaces, and never falls back to a plausible
kind. V1.5 routes packet concept naming through it.

The fallback namer is NOT modified: it belongs to the frozen V0.9/V0.10
line that Tier A depends on, and Tier A's 0.000 wrong-fire over 10,160
traps is the baseline this version is measured against.


---

## B26 — the conflict rule fired on lists, not contradictions

With evidence-backed naming in place, CONFLICTING rose to 22.5% of real
packets. 81 of those 90 were `count` quantities, and every one
inspected was false:

    "Seven red apples and two green apples"        two things
    "12 packs of cookies and 16 packs of noodles"  two things
    "It lasts 1 hour and 30 minutes"               one compound duration
    "Michael arrives at 8:30"                      one clock time

The rule keyed on (entity, concept, time_context, polarity) and fired
whenever two quantities shared that key with different values. The
everyday lexicon names every countable `count`, so any clause listing
two countables collided.

**A genuine conflict is the text ASSERTING TWICE and disagreeing.**
Asserting twice takes two assertions, so two clauses. Two numbers
inside one clause are a list or a compound, never a contradiction.
Adding the clause requirement removed the entire false class:
CONFLICTING 22.5% -> 0.5%.

---

## Discipline note — completeness landed on the threshold, and what that does NOT mean

After B25 and B26 the packet-completeness figure is **15.2%**, against
a coverage threshold of **15%** frozen in the plan. That proximity is
uncomfortable and is recorded rather than glossed.

Two things keep it honest.

First, both fixes were made for defects that were documented
independently of the threshold: B25 because the namer assigned
`payback_months` to snow depth 131 times, B26 because a conflict class
was 100% false positives. Neither was reached for because a number was
short of a bar, and the progression is recorded in full -- 8.2% loose,
5.0% with fabricated concepts, 9.2% regrounded, 15.2% clause-aware --
so anyone can see which change moved what.

Second, and more importantly: **packet completeness is NOT deterministic
coverage.** It is an upper bound on it. A COMPLETE packet still has to
index into the substrate, admit a path, execute, and pass the
validator, and V1.4's lesson is that each of those stages loses
material. The threshold in the plan is on COVERAGE -- queries answered
correctly with no model call -- and that number is not yet measured.

No claim against the coverage threshold is made from this figure.
