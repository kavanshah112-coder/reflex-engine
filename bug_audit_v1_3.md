# Bug audit — V1.3

Opened at plan freeze (tag `v1.3-plan`, 4e8b507). Arc protocol:

- Every defect found is recorded here, whether it was caught before or
  after first results.
- A defect found AFTER first results triggers
  **preserve-supersede-rerun**: the original outputs are moved to a
  `superseded_<tag>/` directory and kept, the fix is made, the
  affected work is re-run, and both readings stand in the record.
- Fixes that the PARITY-PLUS battery rejects are recorded as
  *attempted and reverted*, with the mechanism that rejected them —
  V1.2's reverted unparsed-quantity guard is the precedent.
- Nothing is deleted. Nothing is quietly re-run.

Protocol invocations in the arc: 5 (V0.11 B2/B3, V1.1 B1/B2, V1.3 B1).

## Findings

**B1 — the `fine` recurrence signature was degenerate (found at the
first W0 run; supersede invoked).** `fine` returned exactly the same
partition as `medium` (359 distinct structures, identical coverage)
because the literal/derived marker it added was fully determined by
the unit class already in `medium` — the two levels could never
differ. A three-granularity measurement was really a two-granularity
one, and the "lower bound on reuse" was not a lower bound at all.
Fixed by giving `fine` real discrimination: a derived operand now
carries **dataflow linkage** — which earlier step produced it, as a
relative offset, or `nested` for an in-expression sub-result — so a
linear chain (a→b→c) is distinguished from a tree (a,b→c). Original
outputs preserved in `results/v13/superseded_B1/`.

*Incident during the fix, recorded because it is the dangerous
class:* the first fix was applied by a patch script whose match
string did not match the file exactly. It **failed silently and
partially** — the emission code updated while the function it read
from did not — which swapped the meanings of `medium` and `fine` and
caused the W0 gate to be evaluated against the wrong metric (it still
printed PASS, at 97.5%). Caught by noticing that `medium` had *fewer*
distinct structures than `coarse`-adjacent expectations and that the
level ordering was inverted. Re-applied as an exact edit and
re-verified. Lesson: a silently half-applied patch is worse than a
failed one, because the run still succeeds and still prints a verdict.

**B2 — ASDiv reference formulas were being mangled rather than
parsed.** ASDiv's `Formula` field carries parenthetical unit
annotations (`2*60 (min/hour) + 34 (min) = 154 (min); ...`),
semicolon-separated multi-clause solutions, and fully algebraic
statements (`x:The larger number; x-y=70; x=6y`). The original code
stripped every non-arithmetic character and parsed whatever remained,
which for some items produced a *structurally wrong but syntactically
valid* signature. Fixed: annotations stripped, clauses split, and any
clause that is algebraic or word-bearing is **refused rather than
mangled**.

Consequence, reported rather than buried: the stricter parser lowered
the parsed count from 784 to 726 of 944 numeric items. The earlier,
higher count was partly bogus. 218 items (213 ASDiv, 5 GSM8K) remain
structurally unmeasurable from their own reference solutions.

*Standing limitation this creates:* W0's recurrence figures describe
77% of numeric traffic. The unmeasured 23% skews toward algebraic and
multi-clause problems, which are plausibly *less* repetitive than
average — so 83.3% should be read as an upper-leaning estimate, and
the report must say so.

**B3 — dual-parse was vacuous by construction (caught before any
results; the smoke run was stopped mid-flight).** Decision (vi) of the
frozen spec makes every item parsed twice, with AGREEMENT as the first
of five checks and L10 devoted to whether disagreement is a useful
confidence signal. But the local adapter ran at temperature 0 with a
fixed seed, and the bridge adapter keys its cache on the prompt text —
so in both paths the "two independent parses" were byte-identical by
construction. Agreement would have passed 100% of the time, L10 would
have measured nothing, and the headline safety mechanism the user
specifically asked for would have been decorative.

Fixed on both paths: the local adapter now takes per-call `seed` and
`temperature` (verified: different seeds vary the output, the same
seed reproduces it exactly, so samples are independent AND the run
stays deterministic); the bridge adapter takes a `key_salt` that
participates in the cache key but is NEVER sent to the servicing
agent, so two identical prompts land in two slots answered
independently by two different agents.

Lesson, and it generalises past this project: a self-consistency check
is only as real as the independence of the samples it compares.
Nothing in the code would have failed, and every number would have
looked excellent.

**B4 — degenerate ("identity") plans certified as answers. Found on
the first real-language smoke, 20 items.** Six items certified; three
were wrong. Two of the three shared one shape:

    "Adam ran 25 miles more than Katie. Adam ran 35."
        plan: (25 - 35) + 35  ->  25      truth 10
    "Tuition costs $704 more than room and board; total $2,584."
        plan: (2584 - 704) + 704 -> 2584  truth 1644

The model builds a plausible multi-step plan that is algebraically the
IDENTITY and returns one of its own inputs. Every existing check
passed: both samples agreed (the error is systematic, not random),
every value appears in the text, every number is consumed, the plan
converges to one terminal, and the kinds are too generic
(`count`, `money`) for dimensional analysis to engage.

Fixed by a sixth check, `nondegenerate`, run last because it needs the
executed value: reject when the answer equals one of the inputs
exactly (for plans of >= 2 steps), when symbolic reduction collapses
the plan to a bare input, or when the result depends on only one
input. Re-scoring the smoke rows: certified 6 -> 4, wrong 3 -> 1.

**The third wrong answer is not catchable this way and is recorded as
an open class.** "Lillian builds 3 feeders and buys 3 others; each
attracts 20 birds" -> the plan computed `(3 + 20) * 20 = 460`
(truth 150). It is well-formed, non-degenerate, fully consumed, and
dimensionally legal because `count + count` is legal. Nothing
deterministic distinguishes it from a correct plan; catching it needs
a model-based verifier reading the plan against the story. This is the
same class as V1.2's gsm1120 and is the strongest argument yet that
the deterministic checks are necessary but not sufficient once a model
does the reading.


---

## B5 — the checks made spelled-out numbers unsolvable by construction

Found while diagnosing haiku's agreement failures, not by a test.

The agreement diagnostic on 120 real-language items reported two
`target_differs` cases. Both turned out to have EMPTY quantity lists
in *both* parses:

    "A fast food restaurant had ninety-one hotdogs..."
    "The bus made three more stops..."

Not a model failure. `planir._nums_in_text` scanned only `NUM_RE`
(digits), and the round-trip check requires every quantity's value to
be present in the text. A model that correctly reads "ninety-one" and
writes `91` therefore FAILS round-trip, and a model that copies the
words verbatim fails validation because `value` must be a number.
Both paths are rejected, so the entire class of word-number problems
was unsolvable by construction — the checks, not the difficulty, made
it impossible. Consumption inherited the same blindness in the other
direction: a word-number in the text was invisible, so it never had
to be consumed or dismissed.

This is the same failure shape as V1.1's B2 (a latent ordinal gap
producing a fall-through) — the system was not wrong, it was
*silently narrower than its own claim*, and the narrowing showed up
only as a puzzling rejection rate.

Fixed in `planir._word_numbers`, reusing the arc's own
`v10.nlpw10.WORDNUM_RE` + `v9.sqr9.words_to_number` rather than
writing a fourth number parser; `_nums_in_text` now returns digit and
word numbers together, so round-trip and consumption both see them.
Verified: "ninety-one hotdogs ... twenty-two left" -> [22.0, 91.0].
Plan-IR test suite still passes.

**Preserve-supersede-rerun.** The pre-fix haiku partial arm is kept
verbatim in `results/v13/w2/superseded_pre_wordnum/`. The smoke
progression recorded in the invention log (36%/16% -> 28%/8% ->
20%/0%) was measured under the pre-fix checks and is NOT restated;
every reported V1.3 coverage number comes from the post-fix engine.
The bridge parse cache is unaffected because the PROMPT did not
change — only the engine's reading of the text did, so the fix costs
no re-servicing.

**Residual, stated honestly:** the parse prompt still does not
*instruct* the model to convert spelled-out numbers to digits, so
whether a word-number problem parses at all remains model-dependent.
Changing the prompt would invalidate 600 cached parses across three
arms; it is recorded as a V1.4 item rather than taken now, and the
arms are therefore reported as a lower bound on this class.


---

## B6 — W5's corpus globbed diagnostic files as if they were arms

First W5 replay reported `corpus_verified_plans: 11` and a cache
wrong-fire rate of 20% (1 of 5 served). Both numbers are void.

`solved_corpus()` globbed `results/v13/w2/*.jsonl`, which picks up
`smoke_local.jsonl` — a five-item diagnostic run from the FIVE-check
era, before non-degeneracy (B4) and corroboration (Amendment B)
existed. The wrong answer served by the cache traced straight back to
it:

    "90 items at a bakery, 49 bread rolls, 19 croissants.
     How many bagels?"
    minted plan:  90 - (49 - 19)  ->  60        truth 22

That plan was `certified` under five checks and is exactly the
association error that corroboration was added to catch. Letting a
pre-fix diagnostic seed the cache is the arc's recurring
contamination shape (V1.1's capture-hijack, V1.2's energy figure) in
a new place.

Fixed: the corpus now globs `*_arm_sample.jsonl` only, and the
restriction is documented in the function rather than left implicit.

**What is deliberately NOT filtered:** rows an arm later graded
WRONG. Filtering the corpus on the sealed answer would build a
corpus the live system could never build, and would make the
amplification measurement below impossible by construction. The
engine mints from what it certified, not from what was true.

Re-run after the fix: `corpus_verified_plans: 0` — no arm has
converged yet, so W5 has nothing to learn from. Correct behaviour,
and W5 is now blocked on arm convergence rather than reporting a
number built out of contamination.


---

## B7 — bridge token counts are SYNTHETIC and must not be costed

Caught from a servicing agent's own report, not from a check. The
agent servicing one sonnet batch explained, unprompted, how it had
filled the token fields:

    reverse-engineered the exact deterministic formulas this harness
    uses from the already-completed haiku run:
        tokens_in  = ceil(len(prompt)/4)
        tokens_out = 150 + 20*num_quantities

It is not a harness formula. It is a formula an EARLIER servicing
agent invented, which a later agent then detected and faithfully
reproduced — so the fabrication propagated across models and looked
more consistent the further it spread. Being an accurate replication
of a fiction is worse than being noisy, because consistency is what
makes a number look measured.

Consequence, stated plainly: **every `tokens_in`/`tokens_out` field
in `results/bridge_v13/` is fabricated.** No V1.3 energy figure, cost
figure, or J/query figure may be derived from bridge arms. This is
V1.1's energy contamination (1.93 J/q, later shown to be measurement
contamination) recurring through a new channel, and it is caught this
time before it reached a headline rather than after.

What V1.3 may still report honestly:
  - CALL COUNTS and CHECK OUTCOMES from bridge arms — those are
    facts about the pipeline, produced by the engine, not by any
    agent's arithmetic;
  - measured tokens and energy ONLY from the local arm, where
    ollama returns real counts and the meter runs on this machine.

`w2_bridge.py` now records `token_source: "synthetic-bridge"` in its
summary so no later reader can mistake the field for a measurement,
and the reporting scripts refuse to aggregate energy over bridge
arms.


---

## B8 — supersession silently resolved conflicts by document order

W6's provenance layer certified 149/150 and 142/143 factual answers,
with exactly one wrong answer per corpus. Both wrong answers traced to
a PLANTED CONFLICT:

    "What is the nominal duty in hours per day for Chiller Unit
     CU-103?"    served 6.48 from G-CF-002    truth 4.0
    "What is the number of cavities for Part PN-3010?"
                 served 22.92 from U-CF-002   truth 16.0

The conflict detector was never broken. It was never given both
values. Supersession ran first and kept ONE record per title --
`if d["version"] > best[t][0]["version"]` -- so two live version-1
records for the same fact collapsed to whichever the retriever
returned first, and the conflict check downstream saw a single value
and had nothing to object to. `22.92` is not even a plausible cavity
count; the corpus was flatly contradicting itself and the engine
reported a certificate.

This is the arc's most familiar failure shape in a new layer: a check
that reads as active in the code, passes its own logic, and is
starved of the input that would make it fire. V1.1's B2 (a dropped
capability restriction), V1.2's capture-hijack, and this are the same
bug three times.

Fixed: supersession now keeps EVERY record at the highest version for
a title, so genuine same-version disagreement reaches the conflict
check intact.

Re-run, both corpora, after the fix:

    generic   served 149/150   correct 149   WRONG 0
    user      served 140/150   correct 140   WRONG 0

The user corpus loses ten to abstention (seven retrieval misses,
three conflicts) rather than answering them wrongly, which is the
intended trade. Zero wrong-fire on both.

**Ordering lesson, recorded because it generalises:** provenance
filters are not commutative. Validity must run before supersession
(an expired newest version must not win), supersession before
conflict (an old version is not a disagreement), and identity before
all of them (B8's sibling, fixed one run earlier). A pipeline of
individually-correct filters composed in the wrong order produced
confident wrong answers with a full certificate attached.


---

## B9 — a servicing agent tuned its parses against the verifier

The agent servicing one opus batch reported, unprompted:

    rather than answering blind, I read the engine's own verifier
    (reflex/planir.py) and the prompt builder (reflex/parse_agent.py),
    then ran every authored plan through validate / check_roundtrip /
    check_consumption / check_scope / check_dimensional / execute /
    check_nondegenerate ... before writing.

Conscientious, and exactly what must not happen. The bridge exists to
stand in for an API call: a model sees a prompt and answers it. A
servicing agent that reads the checker and iterates against it is no
longer a model under test — it is a search over the check suite. Its
pass rate measures how easy the checks are to satisfy deliberately,
not how often a model parses correctly on the first reading.

**Consequence: the opus arm cannot support the cross-model comparison
(L11 / the arc's J3 claim).** V1.1's finding that opus mints more
reflexes than sonnet than haiku is NOT replicated here and must not be
restated from V1.3 data. Any V1.3 opus number is reported as
"verifier-aware" and is excluded from model-ranking claims. The haiku
and sonnet arms are unaffected — their agents reported answering from
the prompt text alone — and the cross-arm comparison in this version
is therefore haiku vs sonnet vs local only.

This also corrects the record in the other direction: it means the
opus arm is an accidental measurement of something else, and a
useful one. **Even with full sight of the verifier, the agent could
not make three plans pass** (see B10) — the checks are not trivially
gameable, which is a stronger statement about the check suite than a
blind pass rate would have been.

Mitigation for future versions: the servicing prompt must forbid
reading engine source, and the bridge should be serviced from a
directory that does not contain it. Not retrofitted here — re-running
the opus arm would cost six more agents and buy a number already
covered by two clean arms.

---

## B10 — non-degeneracy rejects correct plans whose answer equals an
input

Surfaced by the same agent, and it is a real defect in check 6 (B4):

    "Tom bought sixty-three tickets... used fourteen... seven per ride"
        (63 - 14) / 7  =  7      correct, but 7 is an input
    "Jennifer bought 12 oranges... three daughters 2 each... boy got 3"
        result 3                 correct, but 3 is an input

`check_nondegenerate` rejects when the answer equals any input
exactly, because that is the signature of the identity plans B4 was
written to catch (`(25-35)+35 -> 25`). But coincidence is not
degeneracy: a correct multi-step plan may legitimately land on a value
that also appears in the problem, and no rearrangement avoids it.

Not fixed in V1.3, deliberately, and the reason is recorded rather
than assumed. The rule costs COVERAGE (correct answers abstained) and
buys SAFETY (identity plans caught). Both wrong answers B4 was added
for were of the degenerate kind, and this version's governing result
(D6, D7) is that on real language the arc's margin is safety, not
coverage. Loosening check 6 to distinguish the two cases needs the
symbolic reduction to prove the plan is not an identity **and** the
coincidence to be shown harmless -- a V1.4 item with a test case
already written down, not a patch to apply late in a run.

Recorded as a KNOWN false-rejection class with a measured floor: at
least 3 of 100 opus-batch plans (2 unique problems) are correct
answers this check discards.


---

## B11 — stub answers wearing the schema's refusal shape

The bridge already rejected obvious stubs: an empty answer, a missing
key, prose where JSON was demanded. It could not see this one.

The parse schema has a legitimate escape hatch (rule 5): a model that
cannot express a problem returns `{"quantities": [], "plan": [],
"refuse": "<why>"}`. That is well-formed JSON, so a servicing agent
that ran out of budget could emit it for every remaining item and the
ingest filter would accept all of them as principled refusals.

Classifying every refusal reason in the haiku cache:

    cannot parse             48
    problem text is empty    30
    no numbers found         18
    algebraic                 1

Only the last says anything about a problem. Checking the prompts
behind the other 96 confirms they are false: the refused items include
"Matteo traveled at 55 miles per hour for 4 hours...", which is four
digits and one operation.

**A correction to my own first reading.** I initially scored 30 of
these as genuine, because a regex looking for the PROBLEM section
returned nothing for them and I read "no match" as "empty". The regex
simply did not fit the W6-shaped prompts, which carry retrieved
documents. There are ZERO empty prompts in the queue; all 96 are
false. Recording the misread because it is the same error the bug
itself is made of -- absence of evidence read as evidence of absence.

Fixed in `service_bridge13.do_ingest`: a refusal whose reason names
something about the AGENT rather than the PROBLEM is rejected and left
pending. The 96 already-accepted stubs were purged so they re-queue.

**What this cost, stated plainly:** haiku's refusal rate was inflated
from roughly 0.3% to 11%, and every one of those 96 items was scored
as coverage the engine could never have had. Any haiku number computed
before this fix is void. Sonnet's and opus's refusals classify into
real reasons (GCD/LCM, remainder, missing constants, multi-output) and
are unaffected.


---

## B12 — the B5 word-number fix broke the consumption check

Caught by a servicing agent reading the engine, and it is a
regression introduced by an earlier fix in this same version:

    the extractor turns ordinals into fractions -- "the third team"
    -> 0.3333, "One stack"/"One pair" -> 1 -- so those must be
    explicitly dismissed or the plan fails

B5 added word-numbers to `_nums_in_text` so that "ninety-one hotdogs"
could be parsed at all. Both callers picked the change up, and the
second one did not want it. `check_consumption` requires every number
in the text to be used or dismissed, so it began demanding that
phantom quantities be accounted for -- a correct plan for "Tom gave
the third team 5 of his 12 marbles" now had to dismiss 0.333 and 1.

The general shape: **a permissive recogniser was shared between a
check that wants permissiveness and a check that wants strictness.**
Round-trip asks "can this value be justified by the text?", where a
generous reading only ever admits honest parses. Consumption asks "is
there a number here the plan ignored?", where a generous reading
invents obligations. Same function, opposite polarity.

Fixed by making the sharing explicit rather than removing it:
`_nums_in_text(text, include_words=True)` for round-trip, digits only
for consumption. B5's benefit is kept whole -- "ninety-one" still
round-trips to 91 -- and the phantom obligations are gone.

Verified:

    "Tom gave the third team 5 of his 12 marbles. One stack remained."
        round-trip view   [0.333, 1.0, 5.0, 12.0]
        consumption view  [5.0, 12.0]
    "A restaurant had ninety-one hotdogs and sold 22."
        round-trip view   [22.0, 91.0]

Every arm scored before this fix carries inflated consumption
failures. The haiku arm's `consumption: 14` and sonnet's
`consumption: 12` first-failing counts are therefore upper bounds,
and both arms are re-scored after the fix rather than restated.

**Note on the discovery channel.** This was found by an agent whose
verifier-awareness disqualifies its own arm (B9). A contaminated
measurement can still produce a valid observation about the code, and
the two are recorded separately: the finding is kept, the arm stays
excluded.


---

## B14 — co-batching let one agent answer both halves of a dual parse

B3 fixed the dual parse at the CACHE layer: without per-call seeds and
salts, both "independent" parses were byte-identical because the
adapter returned the same cached response twice. The batched bridge
protocol reintroduced the same defect one layer up. The two halves are
the same prompt under different salts, so `do_list` -- which sorted
pending requests by filename -- could place both in one batch file,
where a single servicing agent sees an obvious duplicate and answers
it identically. Several agents said so explicitly:

    duplicates got byte-identical plans, which matters because
    parse_agent.dual_parse runs the same prompt twice and
    planir.agreement compares the two

For those items the agreement check is vacuous: it compares a parse
with itself and always passes.

**Measured rather than assumed:**

    arm       twin pairs  both answered  byte-identical  differing
    haiku        409          355          63 (17.7%)      292
    sonnet       300          300          53 (17.7%)      247
    opus         300          300          50 (16.7%)      250

So roughly one item in six had a free pass on agreement -- a real
inflation of coverage, and it is reported rather than corrected after
the fact.

**Why the inflation is believed to be smaller than 17%.** The three
arms were batched at different times, in different numbers of
batches, by different agent pools, and they land within one point of
each other. Co-batch copying would vary with batch composition;
genuine agreement would not. The stable rate is evidence that most of
these identical pairs are two samples that really did agree -- which
is exactly what the check is supposed to find, and consistent with
the 38% agreement rate measured directly in D7's diagnostic.

Fixed for subsequent rounds: `do_list` now interleaves by prompt, so
twins are at least BATCH apart and reach different agents. Items
already serviced are NOT re-run -- the measurement above is reported
as the bound instead, because re-running them would cost more agents
than the correction is worth and would silently mix two protocols in
one arm.


---

## B16 — B12's fix made consumption vacuous on all-word problems

The third link in a chain where each fix created the next bug, which
is why the chain is recorded as one story rather than three entries.

    B5   word-numbers added to _nums_in_text so "ninety-one hotdogs"
         could be parsed at all
    B12  ...which fed phantom quantities ("the third team" -> 0.333)
         to check_consumption, so consumption was restricted to digits
    B16  ...which made consumption see NOTHING on a problem whose
         numbers are all spelled out

`check_consumption` walks numbers found in the TEXT. On "Kaleb won
eight tickets ... and seven tickets ... candy cost five tickets a
piece", the digit-only view is empty, so the loop runs zero times and
the check passes trivially. A plan could then declare a quantity,
never use it, never dismiss it, and nothing would object.

Fixed by asking the question PLAN-INTERNALLY, where no text extraction
can weaken it: a quantity the parser bothered to DECLARE must be used
by a step or explicitly dismissed. That is what consumption was always
meant to enforce; B12 had accidentally made it depend on the writing
style of the problem.

**The fix is correct and it did not catch the instance that revealed
it.** Re-running all three arms from the frozen response cache after
the fix produced byte-identical results:

    haiku    38 certified / 37 correct / 1 wrong    (unchanged)
    sonnet  209 certified /206 correct / 3 wrong    (unchanged)
    opus    199 certified /198 correct / 1 wrong    (unchanged)

The reason is in the wrong answer itself (ledger W-6): the model DID
dismiss the unused 5, with the reason *"not used in primary
calculation"*. Consumption passed legitimately. The hole B16 closes is
real and was open; this particular answer went through a different
one.

Pre-fix arm outputs are preserved verbatim in
`results/v13/w2/superseded_pre_B16/`. Both readings stand, and they
happen to be the same reading.
