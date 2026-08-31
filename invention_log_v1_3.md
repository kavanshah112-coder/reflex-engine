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
