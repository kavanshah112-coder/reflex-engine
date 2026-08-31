# V1.3 wrong-answer ledger

Every certified-but-wrong answer produced anywhere in V1.3, with its
cause and what was done about it. Nothing here is excused, and
nothing is removed once the cause is fixed -- superseded entries keep
their original reading alongside the corrected one.

---

## W-1  "three times more" -- REPLICATED ACROSS TWO MODELS (OPEN)

    "After scoring 14 points, Erin now has three times more points
     than Sara, who scored 8. How many points did Erin have before?"
    served 10.0   gold 18.0   corroborator 10.0

All seven checks passed. The plan (3 x 8 = 24, minus 14) is a
faithful execution of one reading of an ambiguous English idiom; the
dataset uses the other (8 + 3 x 8 = 32, minus 14). The corroborator
agreed with the plan because it is the same model and shares the
reading.

**Replicated.** The sonnet arm -- a clean arm, no verifier
awareness, serviced by different agents in different batches --
produced the SAME wrong answer on the SAME item:

    opus     served 10.0   corroborator 10.0
    sonnet   served 10.0   corroborator 10.0    gold 18.0

Four independent samples across two model families, all four reading
"three times more" as 3x. This is what makes it a class rather than a
slip: the misreading is model-invariant, so no amount of resampling
-- within OR across the models available here -- would surface it.
D11's proposed remedy (cross-model corroboration) is weakened by this
replication and must be re-scoped: a second MODEL helps only where the
models differ, and on common English idioms they do not.

CAUSE: interpretive, not structural. See D11.
STATUS: OPEN. Not fixable by any deterministic check, and NOT fixable
by more resampling of the same model. The V1.4 remedy is cross-model
corroboration; it is not retrofitted here because changing the
corroborator mid-run would mix two protocols in one arm.
CLASS: ambiguous quantifier idioms ("times more", "as much again",
"half again as many"). A detector for these phrases that forces
abstention is a candidate mitigation with a measurable coverage cost.

---

## W-4  non-integer answers under an integral target (OPEN, CATCHABLE)

TWO instances, both from the clean sonnet arm:

    "9 boys ... 29 trees ... each watered the equal amount ...
     how many trees did each boy water?"
        served 3.2222...  gold 3.0   (needs FLOOR)
    "Jane can arrange 16 vases a day. 248 vases. How many days
     are needed to finish?"
        served 15.5       gold 16.0  (needs CEILING)

Both plans are a single faithful `div`. Both declare `target.kind =
count`. Both serve a non-integer as a count. The plan IR has no
integer division (D10), so the exact quotient is the only expressible
answer, and both certified.

Note that the two need OPPOSITE roundings -- one floors, one ceilings
-- which is precisely why the remedy must be abstention and not
rounding. Nothing in the plan says which way the world goes.

CAUSE: the same signature as W-1. Every deterministic check passed on
a well-formed plan; the corroborator agreed because it is the same
model reading the same English the same way (D11).

**This one is catchable, and by a rule the arc already believes in.**
The target kind is `count`. A count is an integer. Serving 3.222 as a
`count` is a TYPE violation, detectable with no model and no
semantics -- the same shape of argument as the dimensional gates the
arc has run since V0.3.

PROPOSED (V1.4, deliberately NOT implemented here): check 8, TARGET
INTEGRALITY -- if the target kind is integral (`count`, and any kind
declared integral in the pack), the executed value must be an integer
within tolerance, else ABSTAIN (never round). Implementing it now
would be tuning on a sealed evaluation, which this arc does not do.

**Measured value of the proposed check, on the clean arm:** it would
have abstained on 2 of the 3 wrong answers, taking sonnet's wrong-fire
from 3/173 (1.73%) to 1/173 (0.58%), at a coverage cost that is
currently unmeasured and must be measured before adoption -- every
legitimate fractional answer under a `count` target would also be
lost.

---

## W-6  haiku arm, vacuous dismissal (OPEN -- new class)

    "Kaleb won eight tickets playing 'whack a mole' and seven tickets
     playing 'skee ball'. If he was trying to buy candy that cost
     five tickets a piece, how many could he buy?"
    served 15.0   gold 3.0   corroborator 15.0

    quantities  q1=8, q2=7, q3=5
    plan        add(q1, q2)            -- one step, stops early
    dismissed   {"value": 5, "reason": "not used in primary
                 calculation"}
    target      {"kind": "count", "scope": "total amount"}

The plan computes the ticket TOTAL and never divides by the price. The
number it needed is sitting in `dismissed`, discarded with a reason
that is circular: it says the five is not used because it is not used.

Every check passed, and consumption passed **legitimately** -- the
number was accounted for, exactly as the schema permits. The escape
hatch that exists so a parser can honestly set aside a distractor was
used to set aside the operative quantity.

Two deterministic signals were available and neither is currently
read:
  - the `target.scope` the model wrote is "total amount", while the
    question asks how many candies could be bought. The plan answers
    its own declared scope and the declared scope answers the wrong
    question;
  - the dismissed quantity is the one introduced by the question's
    final clause, which in "how many X can he buy" problems is
    almost always operative.

CAUSE: not a check failure -- a check-COVERAGE failure. Nothing scores
the QUALITY of a dismissal reason or the FIT of the declared scope to
the question.
STATUS: OPEN, new class, and the first V1.3 wrong answer that is
neither interpretive (W-1) nor typed (W-4).
PROPOSED (V1.4): dismissal must cite a span and a role rather than
assert non-use, and dismissing a quantity introduced by the question's
final clause should be refused outright. Both are cheap and both need
their coverage cost measured before adoption.

---

## W-2  W6 provenance, planted CONFLICT (CLOSED)

    "nominal duty in hours per day for Chiller Unit CU-103"
        served 6.48   truth 4.0    source G-CF-002
    "number of cavities for Part PN-3010"
        served 22.92  truth 16.0   source U-CF-002

CAUSE: B8 -- supersession collapsed same-version records to one, so
the conflict detector never saw two values.
STATUS: CLOSED. Fixed; both corpora re-run at 0 wrong on 289 served.

---

## W-3  W5 plan cache, bakery bagels (VOID -- contaminated input)

    "90 items, 49 bread rolls, 19 croissants. How many bagels?"
        served 60.0   truth 22.0

CAUSE: B6 -- the cache corpus globbed a five-check-era smoke file.
STATUS: VOID. The run that produced it is discarded, not corrected;
the mechanism it demonstrated is kept as D8.


---

## W-5  W5 plan cache, ALL served answers (CLOSED -- mechanism retired)

Seven answers served across both traffic modes; seven wrong. Not
instances -- the mechanism. Representative:

    stored   "Mrs. Hilt ... 17 pages ... read 11"   sub(count,count)
    traffic  "Janet bought 2 chocolate, 13 vanilla and 2 strawberry
              cupcakes. How many cupcakes?"
    served 11   truth 17   (similarity 0.642, bound positionally)

CAUSE: text-similarity retrieval plus positional binding attaches a
verified plan to a question it does not answer. Every check passes
because every check asks whether the plan is consistent with the
TEXT, never whether it answers the QUESTION. See D12.
STATUS: CLOSED by retirement, not by repair. Plan reflexes are not
served in V1.3's reported configuration; the measurement is the
result. A threshold raise would trade a 0.2% hit rate for a 0% one
and would not address the defect.

---

## What every OPEN entry has in common

Five wrong answers from the model-parsed path on sealed real
language: W-1 twice (opus and sonnet, same item), W-4 twice (sonnet),
W-6 once (haiku). They fall into three classes -- interpretive, typed,
and coverage -- and they share a signature exactly:

  1. every deterministic check passes, correctly -- the plan is
     well-formed, fully consumed, dimensionally legal, non-degenerate,
     and its values are all in the text;
  2. the CORROBORATOR agrees with the plan to the digit;
  3. the error is in mapping English pragmatics onto arithmetic --
     an ambiguous quantifier in one, an implied integrality in the
     other.

Point 2 is the finding. The corroborator is not an independent
opinion about MEANING; it is a second sample of the same model, and
it fails in precisely the places the parser fails, because both
inherit one reading of the sentence. Corroboration removed the
random errors (58 to 87 abstentions per arm) and left the systematic
ones untouched.

Two remedies fall out, and neither is applied in this version. Their
relative standing CHANGED once W-1 replicated across models:

  - TYPE-LEVEL checks (target integrality) are now the stronger of
    the two. Deterministic, model-free, no extra call, and they cover
    2 of the 5 events outright -- the largest single class.
  - CROSS-MODEL corroboration is weaker than D11 first proposed.
    W-1 produced identical wrong answers from two model families with
    four independent samples, so a second model would not have caught
    it. It remains worth testing for the errors that ARE
    model-specific; it is no longer the headline fix.

The honest summary, across all five: two are cheaply catchable by
typing (W-4), one is catchable by scoring dismissal quality and scope
fit (W-6), and two are a genuine open problem (W-1) -- an English
idiom that every model available here reads the same way and the
dataset reads the other way.

Three of the five would fall to deterministic, model-free rules that
do not exist yet. That is a better position than it sounds: the
remaining class is small, named, and reproducible.
