# V1.3 SPEC — REAL-LANGUAGE COVERAGE VIA THE PARSE/VERIFY SPLIT
## Retrieval typing · NLP parse agent · plan reflexes · agent breeder · RAG integration

Status: DRAFT v2, 2026-08-31 — NOT frozen, nothing runs until issued.
Revises draft v1 with four decisions taken in review:
  (i)   BRIDGE ONLY — no API spend; batched servicing protocol (§2)
  (ii)  the W0 kill switch gates W5 ALONE, never the version (§3)
  (iii) W6 promoted to a full workstream on a realistic product
        domain, carrying the non-arithmetic claim (§9)
  (iv)  TWO-TIER certification — the "never wrong" claim is kept
        where it is earned and qualified where it is not (§10)
Arc discipline carries forward unchanged (V1_2_SPEC §0). Parameters
marked [PLAN] freeze at plan commit.

---

## 1. The thesis this version tests

V1.2 measured the wall precisely: on human-written problems the
engine covers 0% because it cannot READ them — not because it cannot
compute them. Everything here follows from inverting one decision:

  **The model reads. The engine verifies, computes, and certifies.**

The arc measured this split once already (V0.9 SQR: 94% vs 42% on
out-of-family language) and rejected it on economics that no longer
apply — the engine side now costs 21 mJ, so the whole bill is the
parse. What was never built is the machinery that makes an
LLM-supplied reading SAFE, and that is the substance of this version.

The safety property must survive the inversion. Today the engine
cannot be wrong because it refuses what it cannot read. Afterwards, a
coherent MISREADING yields a confidently certified wrong answer
(V1.2's gsm0403 exactly). W3 exists to close that, and §10 exists to
state honestly what the guarantee becomes.

### Pipeline

    query
      -> W1 FRAME    hashed router + retrieval: domain, candidate
                     kinds/caps/constants, k worked examples.
                     NO frame -> abstain/escalate immediately.
      -> W2 PARSE    NLP agent emits a TYPED STRUCTURE + PLAN over the
                     frame's vocabulary. NEVER a value.
      -> W3 VERIFY   round-trip · consumption · scope · dimensional.
                     Fail -> one guided retry -> else abstain.
      -> W4 EXECUTE  engine runs the plan, certifies, emits the
                     certificate (existing machinery).
      -> W5 ACQUIRE  verified solves become PLAN REFLEXES keyed by
                     structural signature; agent breeder tests before
                     activating. (Gated by W0.)
      -> W6 SERVE    certified values answer directly; RAG arms.

Invariant carried from the arc (V0.4: value handoff 66.1% harmful vs
expression handoff 84.3%; V0.8: raw-value interfaces 36-39% vs typed
84%+): **no LLM-supplied number ever enters certified state.** The
agent may name quantities, relations, scopes and operations; the
engine computes every value.

## 2. Compute policy — BRIDGE ONLY (decision i)

All model work goes through the deferred-replay bridge on session
subscription compute. No API keys, no spend. The V1.1/V1.2 bridge
worked but wasted nearly all its budget on file I/O — 40 prompts per
agent at ~80 tool calls and ~100k context. V1.3 uses a batched
protocol [PLAN]:

  ENQUEUE   the harness writes ONE batch file per N=200 requests:
            [{id, prompt, max_tokens}, ...]
  SERVICE   one agent per batch file; it reads that single file and
            writes ONE result file: [{id, text, tokens_in,
            tokens_out}, ...]. Anti-fabrication instructions
            mandatory; the agent must read the batch, never invent it.
  VERIFY    stub rejection: empty text, missing ids, count mismatch,
            or non-JSON where the prompt demanded JSON -> that id is
            re-queued, not silently accepted.
  REPLAY    harness keys results by id and re-runs; iterate until 0
            pending, with a recorded convergence cap.

Expected throughput ~200 items per agent and 8 agents in parallel:
~1,600 serviced prompts per round, minutes not hours. Budget for the
version [PLAN ~2,500 bridge calls total]: parse-arm samples (§5),
breeder proposals (§8), and the RAG baseline arm (§9).

Local llama3.1:8b carries unlimited-volume work (the full traffic
stream) at zero cost and zero bridge load.

## 3. W0 — Structural recurrence (gates W5 ONLY) (decision ii)

Plan reflexes compound only if real traffic RECURS in structure;
V0.11's flat 25k curve is the precedent for what happens when it does
not. But reading real language at all has standalone value, so this
measurement **decides whether the agent breeder runs — it never stops
the version.**

Method, zero model cost: GSM8K reference solutions carry inline
calculator annotations. Extract each item's operation sequence
directly from the reference solution and cluster at three
granularities:

  coarse  = operation sequence only            (upper bound on reuse)
  medium  = operation sequence + operand unit classes
  fine    = full typed plan shape, roles bound (lower bound)

Gate [PLAN]: if at MEDIUM granularity the top 200 structures cover
>= 35% of items, W5 runs as specced. Below that, W5 is reduced to a
recorded null (schemas are still minted and measured, but the
compounding claim is dropped from the ladder) and the finding —
"real traffic does not recur enough for plan caching" — is reported
as a first-class result. All three curves are published either way.

## 4. W1 — Retrieval typing (the frame)

Two tiers, cheapest first: a hashed n-gram router for pack selection
(V0.2 lineage: OOD AUROC 0.993 at ~1/200,000 the cost of embeddings)
plus retrieval over pack vocabulary, constants and worked examples for
the frame body.

Deliverables: (a) frame precision/recall on in-universe items where
the true domain is known; (b) the no-frame abstention signal measured
as a coverage boundary — how often "no relevant frame" is the correct
call; (c) prompt-size reduction (V1.2 sent all ~77 kinds on every
call; frames should send ~15).

Rule, non-negotiable: **the frame is evidence, not authority.** It
narrows the candidate space and nothing else. Dimensional
verification, contradiction detection and W3's checks all still run on
their own terms. If the frame's kinds cannot type every quantity in
the text, that is a signal to widen or abstain — never to drop the
leftovers.

Acceptance: PARITY-PLUS — with frames live, the full V0.5–V1.2
battery holds zero regressions and zero wrong-fire.

## 5. W2 — NLP parse agent

Contract (frozen): input = query + frame. Output = typed structure
(quantities with units, entities, relations, target) + plan skeleton
(ordered typed operations with scopes). Output MUST NOT contain a
computed value. One parse, then verification, then at most one guided
retry carrying the rejection reason.

Arms, sized to the bridge policy [PLAN]:

  P-local    llama3.1:8b — FULL traffic stream (free, unlimited).
             The commercial question: does a cheap parser suffice?
  P-haiku    400-item sample via bridge
  P-sonnet   400-item sample via bridge
  P-opus     400-item sample via bridge
             (the scale comparison, now at the load-bearing layer)

Samples are the same 400 items across arms, drawn from the sealed
splits' companion sample [PLAN], so arm comparison is paired
(McNemar) rather than independent.

## 6. W3 — Misparse verification (the new safety machinery)

Four deterministic checks, all before execution:

  ROUND-TRIP    regenerate a question from the parsed structure; it
                must match the original on quantities, units,
                entities and ask-target.
  CONSUMPTION   every numeric mention is either used by the plan or
                explicitly dismissed with a reason (gsm0403 left
                "30 days" dangling and answered anyway).
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

## 7. W4 — Plan IR and execution

A typed plan is an ordered sequence of operations over state, with the
constructs real problems use and the engine currently lacks:
repetition and multiplicity ("twice a month", "each day", "for 30
days"), scenario comparison (before/after, with/without,
saved = A − B), aggregation scope (per-unit → total, per-day →
per-month) and sequential state update (spend, then earn, then spend).
Every step is dimensionally checked, execution is deterministic, and
the certificate records the whole plan.

## 8. W5 — Plan reflexes + agent breeder (gated by W0)

The unit of reuse becomes a PLAN SCHEMA keyed by structural signature
— not a word. Precedent: V0.5 measured literal caching at a 4% hit
rate against near-total structural reuse, and V0.4's capability-level
breeder is the one acquisition experiment in the arc that ever
succeeded.

Agent breeder (replacing the single-shot miner that failed four
times): given a verified solve it proposes a generalized plan schema,
then TESTS IT ITSELF against held-out items of the same signature, and
submits only what passes. The three-clause gate that V1.2's
dimensional-only gate lacked:

  (a) dimensional validity of every step;
  (b) re-execution reproduces the originating item's answer;
  (c) reproduces correct answers on >= [PLAN 3] held-out items of the
      same signature.

Clause (c) is the semantic check dimensions cannot give — it is what
would have killed V1.2's gsm1120, a dimensionally perfect speed×time
capability that ignored round-trip and frequency.

Measurement: the reuse curve — fraction of traffic served by cached
plans at zero parse cost, over the stream. Direct successor to
V0.11's flat curve.

## 9. W6 — RAG integration + the non-arithmetic proof (decision iii)

Promoted from a bounded afterthought to a full workstream, on a
**realistic product domain** rather than another academic corpus.

Corpus [PLAN]: a hand-built document set in one commercial domain —
equipment specifications, tariffs/rate cards, and invoices (~40
documents, versioned) — plus [PLAN 300] queries with ground truth,
split traffic/sealed. Two query families:
  DERIVED   requires retrieval AND computation ("the pump on page 4
            runs 6 h/day — what does it cost per month at the tariff
            in appendix B?")
  FACTUAL   requires retrieval only (the non-arithmetic case)

Three arms, same corpus and queries:
  R1 RAG-alone         model retrieves and computes (bridge-serviced)
  R2 reflex-in-context certified values injected as text; the model
                       still writes the answer
  R3 reflex-served     the certified value IS the answer; prose
                       optional and non-authoritative

Measures: accuracy, wrong-answer rate, and — the point of the
workstream — whether the guarantee survives each design. Pre-declared
expectation: R2 improves accuracy but forfeits certification, because
a model can ignore or mangle what is in its context; R3 keeps it.

Non-arithmetic claim: FACTUAL answers are served under PROVENANCE
certification (source id, version, validity window, cross-source
conflict detection, staleness quarantine) rather than derivation —
the strategy specced in the V1.0 draft and deferred twice. This is
where the architecture proves it is not arithmetic-bound.

## 10. W7 — Two-tier certification (decision iv)

After this version an answer may depend on a model's reading, so the
external certificate splits rather than overclaims:

  TIER A — self-parsed input (the existing deterministic path).
    Claim unchanged and unqualified: never wrong; certified across
    10,160 trap items and 65 independent seeds; regenerable.
  TIER B — model-parsed input (the new path).
    Claim: verified reading — every answer passed round-trip,
    consumption, scope and dimensional checks; measured wrong-rate
    X% on sealed real language; every failure itemized by class.

`certify.py` is extended to emit both tiers, to fail if Tier A ever
regresses, and to refuse to print Tier B without a current measured
wrong-rate. The one-page external certificate states both, and states
which tier any given deployment runs in.

## 11. Datasets

**Primary (real language).** V1.2's sealed sets are SPENT — evaluated
once, per protocol. V1.3 draws fresh splits from the unused remainder
of the same frozen corpora (GSM8K/ASDiv/SciQ), records the
V1.2-consumed ids and asserts disjointness at generation time
[PLAN: sealed FULL 300 / UNITS 150 / THEORY 100; traffic 3,000 with
recurrence; paired 400-item arm sample]. Hashes and licences already
recorded in results/real/corpus_hashes.json.

**Secondary (product domain).** The W6 corpus above: hand-built,
hashed, versioned, with its own sealed split [PLAN 100 of the 300].

## 12. Hypotheses (freeze at plan commit)

  L1 Real traffic recurs in structure (gates W5 only).
                                              PREDICT uncertain
  L2 Frames improve parse precision and give a reliable no-frame
     abstention signal.                       PREDICT pass
  L3 The parse/verify split lifts real-language coverage from 0% to
     materially non-zero at wrong-fire <= 2%. PREDICT pass — THE headline
  L4 Misparse checks catch constructed misreadings without rejecting
     good parses.                             PREDICT pass
  L5 Plan reflexes COMPOUND: cached-plan share rises over the stream.
                                              PREDICT uncertain
  L6 A cheap parser suffices: P-local within [PLAN 10pp] of P-sonnet.
                                              PREDICT uncertain — the commercial crux
  L7 R3 (reflex-served) beats R1 (RAG-alone) on derived quantities at
     a lower wrong-answer rate, and R2 forfeits certification.
                                              PREDICT pass
  L8 Provenance certification serves FACTUAL queries at wrong-fire
     <= 2% with staleness and conflict caught. PREDICT pass
  L9 PARITY-PLUS: zero regressions and zero wrong-fire on the whole
     legacy battery plus the 65-seed sweep, and Tier A intact.
                                              PREDICT pass

## 13. Outcome ladder (priority F > D > C > B > A)

  A  L3 + L9 + (L5 or L7/L8): the engine reads real language safely,
     and either its coverage compounds or the RAG/non-arithmetic
     extension lands.
  B  L3 + L9, with L5 null and L7/L8 partial: it reads real language
     but neither compounds nor extends — a product with worse
     economics, reported as the headline negative.
  C  L3 fails while L9 and the abstention boundary hold: reading was
     not the whole bottleneck. Report what the parses got right and
     where execution still failed.
  D  Any sealed suite or sweep above the 2% gate, or Tier A regressed
     — a safety regression outranks every coverage claim.
  F  PARITY-PLUS broken by W1–W4 changes.

(The v1 draft's Outcome E is retired: W0 can no longer end the
version, only reduce W5 to a recorded null — decision ii.)

## 14. Deliverables

Batched bridge protocol + frame/router + parse agent + verification
suite + plan IR + agent breeder + RAG arms + provenance certification
· fresh sealed sets with hashes and a disjointness proof · the
hand-built product corpus · three reuse curves · misparse-suite
results · paired parse-model comparison · two-tier certify.py and
certificate · logs (invention / bug / violation) · v1.3-final tag +
snapshot + report + PDF + artifact + memory · run_v1_3_experiment.py.

## 15. Remaining open questions

1. **Product domain choice for W6.** Equipment specs + tariffs +
   invoices as specced, or a domain closer to your actual commercial
   interest (CFD/engineering reports, plastics quoting)? A domain you
   care about costs the same to build and is worth more afterwards.
2. **Traffic realism.** The 3,000-item stream draws with replacement
   from ~1,180 unique items, which manufactures recurrence. Keep it
   (it models a real repetitive workload) or also run a
   no-replacement pass to measure the pessimistic case?
3. **Dual-parse.** Run it as a measured optional tier everywhere, or
   only on items whose single parse fails a check?
