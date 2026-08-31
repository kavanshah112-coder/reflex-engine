# Invention log — V1.3

Hypotheses frozen in V1_3_SPEC.md §12 at tag `v1.3-plan` (4e8b507),
before any V1.3 item was generated. Statuses are filled in as sealed
results land and are never edited afterwards; where a later result
overturns an earlier reading, both entries stand and the overturn is
noted.

Status key: CONFIRMED · PARTIAL · FALSIFIED · NOT TESTED · PENDING.

| # | Hypothesis | Prediction | Status | Evidence |
|---|---|---|---|---|
| L1 | Real traffic recurs in structure (gates W5 scope) | uncertain | **CONFIRMED** | W0 on the traffic pool (sealed never inspected): medium-granularity top-200 structures cover **83.3%** vs a 35% gate; coarse 170 distinct structures cover 100%; fine (with dataflow linkage) 82.8%. Reference solutions parsed, not our engine's reading. Caveat: measured on 726/944 numeric items — see bug_audit B2. **W5 runs as specced.** |
| L2 | Frames improve parse precision; no-frame is a reliable abstention signal | pass | **PARTIAL** | Signal half CONFIRMED emphatically: perfect in/out-of-domain separation — real language scores max 0.273 vs in-universe min 0.801, 0/300 real items above the weakest in-universe item. Narrowing half CONFIRMED in-universe only: 95.2% recall while carrying 3.4 of 77 kinds (95.6% prompt reduction). It cannot yet narrow REAL language, because the index has no labelled real-language rows. Forced Amendment A (frame advises, never gates). |
| L3 | Parse/verify split lifts real-language coverage from 0% at wrong-fire <= 2% | pass — THE headline | PENDING | |
| L4 | The five checks catch constructed misreadings without rejecting good parses | pass | PENDING | |
| L5 | Plan reflexes compound on T-repeat; the T-unique gap quantifies sampling | uncertain | PENDING | |
| L6 | A cheap parser suffices: P-local within 10pp of P-sonnet | uncertain — commercial crux | PENDING | |
| L7 | R3 beats R1 on derived quantities at lower wrong-answer rate; R2 forfeits certification | pass | PENDING | |
| L8 | Provenance certification serves FACTUAL queries at wrong-fire <= 2% | pass | PENDING | |
| L9 | PARITY-PLUS holds; Tier A intact | pass | PENDING | |
| L10 | Parse agreement is a useful confidence signal | pass | PENDING | |
| L11 | Domain familiarity matters: D-user vs D-generic differ measurably | uncertain | PENDING | |

## Discoveries outside the pre-registered set

(Recorded as they occur — the arc's practice is that unplanned
findings are reported with the same prominence as planned ones.)

**D1 — recurrence is much stronger than the design assumed, and it
is concentrated in very simple shapes.** The gate asked for 35% and
the measurement returned 83.3%. But the head of the distribution is
almost entirely two-operand arithmetic on unit-less counts —
`div(count,count)` 60 items, `sub(count,count)` 55,
`sub(unseen,unseen)` 46, `add(unseen,unseen)` 38 — i.e. real
grade-school traffic repeats at the level of "one subtraction of two
plain numbers", not at the level of rich typed plans. This is good
news for plan caching and *bad* news for the assumption that cached
plans will carry much semantic content: a schema for
`sub(count,count)` is nearly contentless, and matching one is close
to matching an operator. The V1.3 report must not quote 83.3% as
"structures reuse" without this qualifier, and W5's reuse curve
should be read against how much of its hit rate comes from these
degenerate shapes.

**D2 — `unseen` is a large operand class (46 + 38 in the top four).**
These are literals in the reference solution that do not appear in
the question text at all: the solution introduces a number the reader
was expected to know or infer. That is a direct preview of what the
parse agent will face, and it means a non-trivial slice of real
problems cannot be solved from the text alone even with perfect
reading.

**D3 — the frame is a free, model-free out-of-domain detector, and
that is worth more than the narrowing it was built for.** Hashed
n-grams with no training, no embedder and no model separate
in-universe from real-language queries with *zero overlap* across 450
items — a 3x gap between distributions (in-universe median 1.000,
real-language median ~0.125). V0.2 measured this family at ~1/200,000
the cost of embeddings and the arc has under-used it ever since. Two
consequences: (i) the engine can know it is off its own map before
spending a single model call, which is exactly the cheap coverage
boundary a commercial deployment needs; (ii) it also means the frame
cannot narrow vocabulary for real language *yet*, because narrowing
requires labelled neighbours and there are none.

**D4 — the frame should bootstrap from the engine's own successes.**
The index is labelled for free by running the engine and harvesting
the kinds it used. So every VERIFIED real-language solve produced by
W2-W4 becomes a labelled real-language row, and real-language framing
improves precisely as real-language solving improves. This is a
self-improving loop the arc has not tried before — and unlike the
four falsified acquisition attempts, it acquires *retrieval evidence*
rather than engine vocabulary, so a bad row degrades ranking rather
than corrupting certified state. Wired into W5.

**D5 — on real language, dimensional checking barely engages.** The
arc's central safety mechanism since V0.3 is dimensional
verification, and V1.2 already narrowed its claim ("dimensional gates
certify physics, not story semantics"). The first real-language smoke
sharpens that into something starker: of the plans that reached the
dimensional check, most had **0-1 of 2 steps dimensionally
verifiable**, because a model reading grade-school English types its
quantities as `count` and `money` — generic kinds that carry no
distinguishing dimension. One wrong answer certified with *zero*
verifiable steps. So on real language the safety burden falls almost
entirely on the STRUCTURAL checks (round-trip, consumption,
non-degeneracy) and on agreement — not on the dimensional machinery
the arc spent eleven versions building. The engine's best safety
mechanism is domain-bound in a way nobody had measured.


**D7 — parse agreement rejects a majority of real-language parses,
and the rejection is real (L10 evidence).** On the haiku arm, 174 of
300 items (58%) failed at the AGREEMENT check — the single largest
loss anywhere in the pipeline. The obvious suspicion was that the
comparison was over-strict: two equivalent parses differing only in
quantity *labels* would be counted as disagreement, and the check
would be destroying coverage for nothing.

Diagnosed on 120 items by decomposing the comparison:

    operations_differ   54   (45%)
    quantities_differ   18   (15%)
    target_differs       2   ( 2%)   <- both degenerate (see B5)
    one_parse_missing    0
    agree               46   (38%)

The dominant term is `operations_differ`: two independent samples of
the *same model* at the *same temperature* on the *same prompt*
produce materially different arithmetic plans for the same problem.
That is not a naming artifact and not a comparison bug — it is the
model genuinely not knowing how to solve the problem, twice,
differently.

This is the strongest single result for **L10**. It also reframes
what the check is for. Agreement was specified as a cheap
self-consistency filter; on real language it is the pipeline's
primary discriminator, and it works for an uncomfortable reason —
the parse step is far less reliable than the arc's generator universe
ever revealed, and a second sample exposes that unreliability for the
price of one extra call.

Read against D6 (what closed the wrong-fire gap was a second
*opinion*, not a better rule) the picture is consistent: on real
language, safety comes from INDEPENDENCE — two samples, two opinions
— while the deterministic checks contribute progressively less as
the language gets further from the engine's home domain (D5). The
arc's eleven versions of dimensional machinery buy less here than one
resample does. That is not the result the spec predicted.


**D8 — plan reflexes multiply the certification error rate by the
reuse count.** B6's void run demonstrated the mechanism cleanly even
though its rate is discarded. A wrong-but-certified plan was minted
into a schema, matched a later identical query at similarity 1.0,
passed every deterministic check a second time (it is dimensionally
legal, fully consumed, non-degenerate — it was always those things),
and was served again.

This is structural, not a bug. The cache mints from what the engine
CERTIFIED, because correctness is not observable at mint time. So a
plan reflex does not merely reuse a solve — it reuses the solve's
error with it, once per hit. Where V1.1 and V1.2 measured wrong-fire
of 0.000, this channel was invisible; on real language, where W2's
wrong rate is not zero, caching converts a one-off error into a
recurring one, and the multiplier is exactly the reuse count that
makes caching worth doing. **The economic case for plan reflexes and
their safety risk are the same number.**

Two consequences, both taken:
  - a cache hit must not be cheaper in CHECKS than a fresh parse,
    only cheaper in PARSING. The one check it structurally cannot run
    is agreement (there is no second parse), which is the strongest
    discriminator on real language (D7) — so W5 is run as an explicit
    ablation, with and without an independent corroboration standing
    in for the missing second opinion;
  - the honest headline for W5 is not the hit rate but the pair
    (hit rate, wrong-fire), and a hit rate bought with a nonzero
    wrong-fire is a worse result than a lower hit rate at zero.


**D9 — the first certified NON-ARITHMETIC answers in the arc.** W6's
R3 arm serves FACTUAL questions with no computation and no model at
all: retrieve, establish identity, quarantine expired sources, drop
superseded versions, require the survivors to agree, and emit the
value with a certificate naming source, version and validity window.

    corpus     served    correct   WRONG   retrieval recall
    generic    149/150   149       0       0.860
    user       140/150   140       0       0.977

Two things are new. First, the arc's guarantee has never before
attached to anything but a derivation -- this is the same abstention
discipline carried onto a value nobody computed, and it holds at zero
wrong-fire on 300 sealed questions across two domains. Second, it
answers the objection that the whole approach is arithmetic-only:
half of W6 is retrieval, and the certified half needs no arithmetic
whatsoever.

**Cross-corpus finding (section 9 asked for this explicitly).** The
user's own domain retrieves BETTER (0.977 vs 0.860) but serves
slightly LESS (140 vs 149). Both come from the same property:
plastics records carry distinctive identifiers (`Part PN-3010`,
`ABS GP-500`) that hashed n-grams separate cleanly, whereas the
generic corpus is full of near-identical names (`Tariff Northland
S0`, `Tariff Eastport S1`) that collide. Better identity means
retrieval finds the right record; it also means the engine more often
notices it has two genuine sources for that record and abstains. So
domain familiarity did not raise accuracy -- accuracy was already
perfect on what was served -- it moved the loss from
wrong-record-retrieved to honest-abstention. That is the direction a
safety-first system should want, and it was not predicted.


**D10 — the coverage ceiling on real language is the plan IR, not the
parser.** Once B11's stubs are removed, the surviving refusals are
principled, and they classify tightly. Across the sonnet and opus
batches the model declines roughly one problem in nine, always for one
of six structural reasons:

    GCD / LCM                    not expressible in add/sub/mul/div
    remainder / modulo / floor   no such operator
    missing world constant       7 days, 4 legs, 100 for a percentage
    multi-output answers         "find the length AND the width"
    conditional logic            "an extra point if over 20"
    clock / calendar arithmetic  wraparound, AM/PM, days in a month

None of these is a reading failure. The model understood every one of
them; the INTERMEDIATE REPRESENTATION cannot hold the answer. V1.3 was
built on the premise that the parser was the bottleneck (V1.2's
closing statement, and the reason for the whole parse/verify split),
and that premise is now only half right: the parser was the bottleneck
for the problems the IR can express, and for about 11% of real word
problems the IR is the wall.

This is a sharper V1.4 problem statement than "improve the parser",
and it is cheap to act on: five of the six classes are new operators
(`mod`, `gcd`, `lcm`, `floordiv`, plus a literal-constant table with
provenance), and each is dimensionally checkable in exactly the way
the arc's existing gates expect. The sixth -- multi-output answers --
is a change to what a plan IS, not what it can do, and should be
scoped separately.


**D11 — sampling independence is not interpretive independence.** The
opus arm certified 104 answers and got exactly one wrong. That one
answer is worth more than the 103:

    "After scoring 14 points, Erin now has three times more points
     than Sara, who scored 8. How many points did Erin have before?"

        plan      3 x 8 = 24,  24 - 14 = 10        served 10
        gold                                       18

The gold reads "three times MORE" as 8 + 3x8 = 32, then 32 - 14 = 18.
The engine's plan reads it as 3x8 = 24. Both readings of that English
idiom are defensible; the dataset picked one.

What matters is which checks fired. **None of them.** Agreement,
round-trip, consumption, scope, dimensional, non-degeneracy -- all
pass, correctly, because the plan is a faithful execution of a
coherent reading. And CORROBORATION passed too: the independent solve
returned 10.0, agreeing with the plan to the digit.

D6 concluded that what closed the wrong-fire gap was a second
OPINION, and that the corroborator "does not need to be right, only
independent". This is the boundary of that claim. The corroborator was
independent in the only sense the design gave it -- a different
sample, a different seed, a different prompt shape -- and it was not
independent in the sense that mattered. **Two samples of one model
share an interpretation prior.** Resampling varies the plan; it does
not vary the reading of "three times more".

So the arc now has a stack of three statements, each narrowing the
one before:

    V1.1  dimensional gates certify physics
    V1.2  ...not story semantics
    V1.3  ...and resampling does not recover semantics either,
          because the second sample inherits the first one's reading

The corollary is concrete and cheap: a corroborator should be a
DIFFERENT MODEL, not another sample of the same one. Cross-model
corroboration is the single highest-value V1.4 change this run
identified, and the bridge already has three models wired up to test
it.

**Honesty note.** This observation comes from the arm that B9
disqualifies for model-ranking claims. A verifier-aware agent produced
the parse, so the 104/1 RATE is not reportable as a model's
performance. The FAILURE MODE is reportable: no amount of
verifier-awareness helped here, because the agent was not fighting the
checker -- it read the English the way the checker's own corroborator
read it, and both were wrong together.


**D12 — plan reflexes do not transfer. The hypothesis is FALSIFIED,
and the way it fails is the arc's oldest failure wearing modern
clothes.** W5 preloaded 203 verified plans and replayed them against
traffic those plans had never seen:

    mode      n      served   correct   WRONG    hit rate
    repeat   3000       6        0        6      0.0020
    unique   1180       1        0        1      0.0008

Seven served, seven wrong. Not a low yield with a small error rate --
a **100% wrong-fire rate on everything the cache dared to answer.**

The clearest instance:

    stored schema   "Mrs. Hilt picked up a book that has 17 pages.
                     She read 11 of them..."        sub(count, count)
    traffic query   "For a party Janet bought some cupcakes. She
                     bought 2 chocolate, 13 vanilla and 2 strawberry.
                     How many cupcakes?"
    similarity 0.642 -> bound positionally -> served 11   truth 17

Two short questions about small counts, lexically similar enough to
cross threshold, semantically opposite: one is a subtraction, the
other an addition. Every check passed. The bound values really do
appear in the traffic text, they really are all consumed, the plan
really does converge on one terminal, `count - count` really is
dimensionally legal, and the result really is not degenerate.

**The checks verify that a plan is internally consistent with the
text. Not one of them verifies that the plan answers the QUESTION.**
That gap was invisible while a parser produced every plan from the
question in front of it -- the plan was about the right question by
construction. A cache breaks that guarantee, and nothing downstream
notices.

This is V0.1's founding failure exactly: retrieval by surface
similarity, confident nonsense out. Eleven versions of checking
machinery sit between then and now, and none of it caught this,
because all of it was built to validate a derivation rather than to
question a premise.

**Consequence for the economic claim.** Section 8 proposed plan
reflexes as the route to serving repeated structure at zero parse
cost, resting on W0's confirmed 83.3% structural recurrence (L1). L1
still stands -- the structures DO recur. What does not follow, and is
now measured, is that a recurring structure can be BOUND to a new
question by text similarity. Structural recurrence is not
interchangeability. The 83.3% is real and unusable by this mechanism.

**What would have to be true instead.** A plan reflex needs a match
on the QUESTION's semantics, not the passage's surface. The only
apparatus in this version that could supply that is the parse itself
-- which is the cost the cache existed to avoid. So plan reflexes as
specified are not a near-miss needing a better threshold; the design
is circular, and V1.4 should either drop them or re-found them on a
cheap semantic signal (the target-kind and operator signature the
frame could predict BEFORE parsing) with the wrong-fire measured
first, not the hit rate.

Recorded as the most useful negative result in V1.3: a mechanism that
looked economically decisive, tested early, and killed cheaply.
