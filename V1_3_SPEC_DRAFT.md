# V1.3 SPEC — REAL-LANGUAGE COVERAGE VIA THE PARSE/VERIFY SPLIT
## Retrieval typing · NLP parse agent · plan-level reflexes · agent breeder

Status: DRAFT authored 2026-08-31 for review — NOT frozen, nothing
runs until issued. Operationalizes the user directive: make it work
with normal human language, make it self-generating, and take it
beyond arithmetic. Arc discipline carries forward unchanged
(V1_2_SPEC §0). Parameters marked [PLAN] freeze at plan commit.

---

## 0. The thesis this version tests

V1.2 measured the wall precisely: on human-written problems the
engine covers 0% because it cannot READ them — not because it cannot
compute them. Everything here follows from inverting one decision:

  **The model reads. The engine verifies, computes, and certifies.**

The arc already measured this split once (V0.9 SQR: 94% vs 42% on
out-of-family language) and rejected it on economics that no longer
apply — the engine side now costs 21 mJ, so the entire bill is the
parse call. What was never built is the machinery that makes an
LLM-supplied reading SAFE, and that is the substance of this version.

The safety property must survive the inversion. Today the engine
cannot be wrong because it refuses what it cannot read. After the
inversion, a coherent MISREADING produces a confidently certified
wrong answer (V1.2's gsm0403 exactly). W3 exists to close that.

## 1. Architecture contract (the new pipeline)

    query
      -> W1 FRAME      hashed router + retrieval: domain, candidate
                       kinds/caps/constants, k worked examples.
                       NO frame -> abstain/escalate immediately.
      -> W2 PARSE      NLP agent emits a TYPED STRUCTURE + PLAN over
                       the frame's vocabulary. NEVER a value.
      -> W3 VERIFY     round-trip · consumption · scope · dimensional.
                       Fail -> one guided retry -> else abstain.
      -> W4 EXECUTE    engine runs the plan step-by-step, certifies,
                       emits the certificate (existing machinery).
      -> W5 ACQUIRE    successful verified solves become PLAN REFLEXES
                       keyed by structural signature; agent breeder
                       tests before activating.
      -> W6 SERVE      certified values answer directly; optionally
                       decorate a RAG context for prose.

Invariant carried from the arc (V0.4: value handoff 66.1% harmful vs
expression handoff 84.3%; V0.8: raw-value interfaces 36-39% vs typed
84%+): **no LLM-supplied number ever enters certified state.** The
agent may name quantities, relations, scopes and operations; the
engine computes every value.

## 2. W0 — THE KILL SWITCH (runs first, gates the whole version)

Plan-level reflexes only compound if real traffic RECURS in
structure. V0.11's flat 25k learning curve is the precedent for what
happens when it does not.

Measurement, zero LLM cost: GSM8K reference solutions carry inline
calculator annotations. Extract each item's operation sequence
directly from the reference solution and cluster at three
granularities:

  coarse  = operation sequence only            (upper bound on reuse)
  medium  = operation sequence + operand unit classes
  fine    = full typed plan shape, roles bound (lower bound)

Pre-registered gate [PLAN]: at MEDIUM granularity, the top 200
structures must cover >= 35% of items. Below that, plan-caching
cannot compound; the version STOPS, reports Outcome E, and the design
is revised before anything is built. All three curves are reported
whatever happens.

## 3. W1 — Retrieval typing (the frame)

Two tiers, cheapest first: a hashed n-gram router for pack selection
(V0.2 lineage: OOD AUROC 0.993 at ~1/200,000 the cost of embeddings)
plus retrieval over pack vocabulary, constants and worked examples
for the frame body.

Deliverables: (a) frame precision/recall on in-universe items where
the true domain is known; (b) the no-frame abstention signal measured
as a coverage boundary — how often "no relevant frame" is the correct
call; (c) prompt-size reduction (V1.2 sent all ~77 kinds on every
call; frames should send ~15).

Rule, non-negotiable: **the frame is evidence, not authority.** It
narrows the candidate space and nothing else. Dimensional
verification, contradiction detection and W3's checks all still run
on their own terms. If the frame's kinds cannot type every quantity
in the text, that is a signal to widen or abstain — never to drop the
leftovers.

Acceptance: PARITY-PLUS — with frames live, the full V0.5–V1.2
battery holds zero regressions and zero wrong-fire.

## 4. W2 — NLP parse agent

Contract (frozen): input = query + frame. Output = typed structure
(quantities with units, entities, relations, target) + plan skeleton
(ordered typed operations with scopes). Output MUST NOT contain a
computed value. One parse, then verification, then at most one guided
retry carrying the rejection reason.

Parse-model arms — this is now the load-bearing layer, so scale is
measured here rather than at the miner [PLAN]:

  P-local   llama3.1:8b (free, unlimited)  — the commercial question
  P-haiku   claude-haiku-4-5               — the cheap plausible one
  P-sonnet  claude-sonnet-5                — the strong one

Volume note: parsing thousands of queries is infeasible through the
deferred-replay bridge (V1.2 needed seven agents for 270 prompts).
This version therefore uses the DIRECT API adapter (built and
verified in V1.1) for parse volume, with the bridge retained for any
Opus-scale replication. See Open Question 1.

## 5. W3 — Misparse verification (the new safety machinery)

Four deterministic checks, all run before execution:

  ROUND-TRIP    regenerate a question from the parsed structure; it
                must match the original on quantities, units,
                entities and ask-target.
  CONSUMPTION   every numeric mention in the text is either used by
                the plan or explicitly dismissed with a reason
                (gsm0403 left "30 days" dangling and answered anyway).
  SCOPE         the plan's time/aggregation scope matches what the ask
                names (per-day vs per-month vs total; single scenario
                vs difference-of-scenarios).
  DIMENSIONAL   existing engine verification, unchanged.

Optional and measured [PLAN]: DUAL-PARSE agreement — two independent
parses must agree on structure — as a stronger, costlier tier.

Acceptance: a constructed misparse suite (correct-arithmetic /
wrong-reading items, built from V1.2's itemized failures and
mutations of known-good parses) must be caught at >= [PLAN 90%] while
known-good parses are rejected at <= [PLAN 5%].

## 6. W4 — Plan IR and execution

A typed plan is an ordered sequence of operations over state, with
the constructs real problems actually use and the engine currently
lacks: repetition and multiplicity ("twice a month", "each day", "for
30 days"), scenario comparison (before/after, with/without,
saved = A − B), aggregation scope (per-unit → total, per-day →
per-month) and sequential state update (spend, then earn, then
spend). Every step is dimensionally checked, execution is
deterministic, and the certificate records the whole plan.

## 7. W5 — Plan-level reflexes + agent breeder

The unit of reuse becomes a PLAN SCHEMA keyed by structural
signature — not a word. Precedent: V0.5 measured literal caching at a
4% hit rate against near-total structural reuse, and V0.4's
capability-level breeder is the one acquisition experiment in the arc
that ever succeeded.

Agent breeder (replacing the single-shot miner that failed four
times): given a verified solve it proposes a generalized plan schema,
then TESTS IT ITSELF against held-out items of the same signature,
and submits only what passes. The three-clause gate that V1.2's
dimensional-only gate lacked:

  (a) dimensional validity of every step;
  (b) re-execution reproduces the originating item's answer;
  (c) reproduces correct answers on >= [PLAN 3] held-out items of the
      same signature.

Clause (c) is the semantic check dimensions cannot give — it is what
would have killed V1.2's gsm1120, a dimensionally perfect speed×time
capability that ignored round-trip and frequency.

Measurement: the reuse curve — fraction of traffic served by cached
plans at zero parse cost, over the stream. This is the direct
successor to V0.11's flat curve and the version's compounding test.

## 8. W6 — RAG integration and the non-arithmetic proof

Bounded workstream [PLAN ~200 items]: a document corpus of facts plus
queries requiring retrieval AND computation ("the pump on page 4 runs
6 h/day — what does it cost per month at the tariff in appendix B?").
Three arms: RAG-alone (model reads and computes), RAG + reflex-in-
context (certified values injected as text), RAG + reflex-served
(the certified value IS the answer, prose optional). Measures:
accuracy, wrong-answer rate, and whether the guarantee survives each
design.

This also carries the non-arithmetic claim: retrieved facts are
served under PROVENANCE certification (source, version, validity
window, conflict detection) rather than derivation — the strategy
specced in the V1.0 draft and deferred twice.

## 9. Datasets (fresh, disjoint from V1.2)

V1.2's sealed real-language sets are SPENT — evaluated once, per
protocol. V1.3 draws fresh splits from the unused remainder of the
same frozen corpora, records the V1.2-consumed ids and asserts
disjointness at generation time [PLAN sizes: sealed FULL 300 /
UNITS 150 / THEORY 100 / RAG 200; traffic 3,000 with recurrence].
Corpus hashes and licences are already recorded in
results/real/corpus_hashes.json.

## 10. Hypotheses (freeze at plan commit)

  L1 Real traffic recurs in structure (the W0 gate).
     PREDICT uncertain — the crux
  L2 Frames improve parse precision and give a reliable no-frame
     abstention signal.                        PREDICT pass
  L3 The parse/verify split lifts real-language coverage from 0% to
     materially non-zero at wrong-fire <= 2%.  PREDICT pass — THE headline
  L4 Misparse checks catch constructed misreadings without rejecting
     good parses.                              PREDICT pass
  L5 Plan reflexes COMPOUND: cached-plan share of traffic rises over
     the stream.                               PREDICT uncertain
  L6 A cheap parser suffices: P-local within [PLAN 10pp] of P-sonnet.
     PREDICT uncertain — the commercial crux
  L7 Reflex-served beats RAG-alone on derived quantities at a lower
     wrong-answer rate.                        PREDICT pass
  L8 PARITY-PLUS: zero regressions and zero wrong-fire on the whole
     legacy battery plus the 65-seed sweep.    PREDICT pass

## 11. Outcome ladder (priority F > D > E > C > B > A)

  A  L3 + L5 + L8 (with L1 passed): the engine reads real language,
     and its coverage compounds as structures recur.
  B  L3 + L8, L5 null: it works but does not compound — every novel
     query costs a parse call. A product with worse economics, and
     the honest negative is reported as the headline finding.
  C  L3 fails while L8 and the abstention boundary hold: reading was
     not the whole bottleneck. Report what the parses got right and
     where execution still failed.
  D  Any sealed suite or sweep above the 2% gate — a safety
     regression outranks every coverage claim.
  E  The W0 kill switch fires: no structural recurrence. The version
     STOPS before building, reports the three reuse curves, and the
     plan-cache design is revised.
  F  PARITY-PLUS broken by W1–W4 changes.

## 12. Deliverables

Frame/router + parse agent + verification suite + plan IR + agent
breeder + RAG arms · fresh sealed sets with hashes and a disjointness
proof · the three reuse curves · misparse-suite results · per-arm
parse-model comparison · certify.py updated to cover the new failure
modes · logs (invention / bug / violation) · v1.3-final tag +
snapshot + report + PDF + artifact + memory · run_v1_3_experiment.py.

## 13. Open questions for review (decide before freeze)

1. **API volume.** Parsing thousands of queries cannot go through the
   bridge. Use the direct API adapter for parse volume (your key is in
   the gitignored .env and verified), keeping the bridge for
   Opus-scale replication? Or restrict V1.3 to the local parser and
   defer the scale arms?
2. **Scope.** W0–W6 is roughly twice V1.2's size. Cut W6 (RAG /
   non-arithmetic) to a follow-on version, or keep it bounded at
   ~200 items as specced?
3. **The W0 bar.** Is ">= 35% of items covered by the top 200
   medium-grain structures" the right kill threshold — or would you
   build the parse/verify half regardless, since L3 (reading real
   language at all) has value even if nothing ever compounds?
4. **Corpus.** Stay with GSM8K/ASDiv/SciQ, or add a domain closer to a
   real product (invoices, engineering specs, lab reports) even though
   ground truth must then be hand-built?
5. **Certification stance.** After this version an answer depends on a
   model's reading. Does the external certificate keep claiming "never
   wrong", qualified by the verification suite — or drop to "never
   wrong on self-parsed input; verified-reading elsewhere"? This is a
   positioning decision, not a technical one.
