# V1.3 SPEC — REAL-LANGUAGE COVERAGE VIA THE PARSE/VERIFY SPLIT
## Retrieval typing · NLP parse agent · plan reflexes · agent breeder · RAG integration

Status: **FROZEN 2026-08-31**, issued by the user. Supersedes
V1_3_SPEC_DRAFT.md (kept for provenance). All review decisions are
recorded below and the hypotheses and ladder (§12–13) are frozen from
this commit, before any V1.3 item is generated. Arc discipline carries
forward unchanged (V1_2_SPEC §0). Parameters marked [PLAN] are frozen
here.

Review decisions folded in:
  (i)    BRIDGE ONLY — no API spend; batched servicing protocol (§2)
  (ii)   the W0 kill switch gates W5 ALONE, never the version (§3)
  (iii)  W6 promoted to a full workstream, on TWO corpora — a generic
         product domain and the user's own commercial domain — so the
         two can be compared (§9)
  (iv)   TWO-TIER certification (§10)
  (v)    BOTH traffic modes — with and without replacement — run and
         compared, so manufactured recurrence is separated from real
         recurrence (§11)
  (vi)   DUAL-PARSE EVERYWHERE, with parse agreement measured as a
         safety signal in its own right (§6)

---

## 1. The thesis this version tests

V1.2 measured the wall precisely: on human-written problems the engine
covers 0% because it cannot READ them — not because it cannot compute
them. Everything here follows from inverting one decision:

  **The model reads. The engine verifies, computes, and certifies.**

The arc measured this split once already (V0.9 SQR: 94% vs 42% on
out-of-family language) and rejected it on economics that no longer
apply — the engine side now costs 21 mJ, so the whole bill is the
parse. What was never built is the machinery that makes an
LLM-supplied reading SAFE, and that is the substance of this version.

The safety property must survive the inversion. Today the engine
cannot be wrong because it refuses what it cannot read. Afterwards, a
coherent MISREADING yields a confidently certified wrong answer
(V1.2's gsm0403 exactly). §6 exists to close that; §10 states honestly
what the guarantee becomes.

### Pipeline

    query
      -> W1 FRAME    hashed router + retrieval: domain, candidate
                     kinds/caps/constants, k worked examples.
                     NO frame -> abstain/escalate immediately.
      -> W2 PARSE    NLP agent emits a TYPED STRUCTURE + PLAN over the
                     frame's vocabulary. NEVER a value. TWICE (§6).
      -> W3 VERIFY   agreement · round-trip · consumption · scope ·
                     dimensional. Fail -> one guided retry -> abstain.
      -> W4 EXECUTE  engine runs the plan, certifies, emits the
                     certificate (existing machinery).
      -> W5 ACQUIRE  verified solves become PLAN REFLEXES keyed by
                     structural signature; agent breeder tests before
                     activating. (Scope gated by W0.)
      -> W6 SERVE    certified values answer directly; RAG arms.

Invariant carried from the arc (V0.4: value handoff 66.1% harmful vs
expression handoff 84.3%; V0.8: raw-value interfaces 36–39% vs typed
84%+): **no LLM-supplied number ever enters certified state.** The
agent may name quantities, relations, scopes and operations; the
engine computes every value.

## 2. Compute policy — BRIDGE ONLY (decision i)

All model work runs through the deferred-replay bridge on session
subscription compute. No API keys, no spend. V1.1/V1.2's bridge wasted
nearly all its budget on file I/O — 40 prompts per agent at ~80 tool
calls. V1.3 uses a batched protocol [PLAN]:

  ENQUEUE   harness writes ONE batch file per N=200 requests:
            [{id, prompt, max_tokens}, ...]
  SERVICE   one agent per batch file; it reads that single file and
            writes ONE result file: [{id, text, tokens_in,
            tokens_out}, ...]. Anti-fabrication instructions
            mandatory; the agent must read the batch, never invent it.
  VERIFY    stub rejection: empty text, missing/extra ids, count
            mismatch, or non-JSON where JSON was demanded -> that id
            is re-queued, never silently accepted.
  REPLAY    harness keys results by id and re-runs; iterate to 0
            pending, with a recorded convergence cap.

Expected ~200 items per agent, 8 agents in parallel: ~1,600 serviced
prompts per round. Version budget [PLAN ~3,500 bridge calls], sized
for dual-parse: parse-arm samples (§5), breeder proposals (§8), the
RAG-alone baseline (§9).

Local llama3.1:8b carries unlimited-volume work (both full traffic
streams, both parses) at zero cost and zero bridge load.

## 3. W0 — Structural recurrence (gates W5 scope ONLY) (decision ii)

Plan reflexes compound only if traffic RECURS in structure; V0.11's
flat 25k curve is the precedent for what happens when it does not. But
reading real language has standalone value, so this measurement
**decides W5's scope — it never stops the version.**

Method, zero model cost: GSM8K reference solutions carry inline
calculator annotations. Extract each item's operation sequence from
the reference solution and cluster at three granularities:

  coarse  = operation sequence only            (upper bound on reuse)
  medium  = operation sequence + operand unit classes
  fine    = full typed plan shape, roles bound (lower bound)

Gate [PLAN]: if at MEDIUM granularity the top 200 structures cover
>= 35% of items, W5 runs as specced. Below that, W5 reduces to a
recorded null — schemas are still minted and measured, but the
compounding claim leaves the ladder and "real traffic does not recur
enough for plan caching" is reported as a first-class result. All
three curves are published either way.

## 4. W1 — Retrieval typing (the frame)

Two tiers, cheapest first: a hashed n-gram router for pack selection
(V0.2 lineage: OOD AUROC 0.993 at ~1/200,000 the cost of embeddings)
plus retrieval over pack vocabulary, constants and worked examples for
the frame body.

Deliverables: (a) frame precision/recall on in-universe items where
the true domain is known; (b) the no-frame abstention signal measured
as a coverage boundary; (c) prompt-size reduction (V1.2 sent all ~77
kinds on every call; frames should send ~15).

Rule, non-negotiable: **the frame is evidence, not authority.** It
narrows the candidate space and nothing else. Dimensional
verification, contradiction detection and §6's checks all still run on
their own terms. If the frame's kinds cannot type every quantity in
the text, that is a signal to widen or abstain — never to drop the
leftovers.

Acceptance: PARITY-PLUS — with frames live, the full V0.5–V1.2 battery
holds zero regressions and zero wrong-fire.

## 5. W2 — NLP parse agent

Contract (frozen): input = query + frame. Output = typed structure
(quantities with units, entities, relations, target) + plan skeleton
(ordered typed operations with scopes). Output MUST NOT contain a
computed value. Parse twice (§6), verify, then at most one guided
retry carrying the rejection reason.

Arms [PLAN], sized for dual-parse under the bridge budget:

  P-local    llama3.1:8b — BOTH full traffic streams (free)
             The commercial question: does a cheap parser suffice?
  P-haiku    300-item paired sample, 2 parses each = 600 bridge calls
  P-sonnet   300-item paired sample = 600 calls
  P-opus     300-item paired sample = 600 calls

The 300 items are identical across arms, so comparison is paired
(McNemar), not independent.

## 6. W3 — Misparse verification, dual-parse everywhere (decision vi)

**Every item is parsed twice, independently.** Agreement is checked
first and is itself a measured signal — a disagreement rate is a
confidence estimator the arc has never had, and disagreement routes to
abstention rather than to a coin flip.

Five deterministic checks, all before execution:

  AGREEMENT     two independent parses must agree on structure
                (quantities, units, entities, target, plan shape).
                Disagreement -> one guided retry -> else abstain.
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

Measured for the report: how much each check contributes
independently — agreement alone, agreement + round-trip, and so on —
so the cost of dual-parse is justified with evidence rather than
assumed.

Acceptance: a constructed misparse suite (correct-arithmetic /
wrong-reading items, built from V1.2's itemized failures and mutations
of known-good parses) caught at >= [PLAN 90%], with known-good parses
rejected at <= [PLAN 5%].

## 7. W4 — Plan IR and execution

A typed plan is an ordered sequence of operations over state, with the
constructs real problems use and the engine currently lacks:
repetition and multiplicity ("twice a month", "each day", "for 30
days"), scenario comparison (before/after, with/without,
saved = A − B), aggregation scope (per-unit → total, per-day →
per-month) and sequential state update (spend, then earn, then spend).
Every step is dimensionally checked, execution is deterministic, and
the certificate records the whole plan.

## 8. W5 — Plan reflexes + agent breeder (scope gated by W0)

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
plans at zero parse cost — computed separately for BOTH traffic modes
(§11), which is what separates real recurrence from sampling artefact.

## 9. W6 — RAG integration + non-arithmetic, TWO corpora (decision iii)

Two hand-built document corpora, identical query design, so a generic
domain and the user's own domain can be compared directly.

  D-generic  equipment specifications, tariffs/rate cards, invoices
             [PLAN ~40 versioned documents, 300 ground-truthed
             queries] — synthetic but realistic; the neutral baseline.
  D-user     the user's commercial domain [PLAN same shape]:
             plastics/manufacturing quoting — material data sheets,
             machine rate cards, cycle times, part weights — with CFD
             report extraction as the documented alternative if
             preferred at build time.

Query families in both: DERIVED (retrieval AND computation — "the pump
on page 4 runs 6 h/day, what does it cost per month at the tariff in
appendix B?") and FACTUAL (retrieval only — the non-arithmetic case).

Three arms per corpus, same queries:
  R1 RAG-alone         model retrieves and computes (bridge-serviced)
  R2 reflex-in-context certified values injected as text; the model
                       still writes the answer
  R3 reflex-served     the certified value IS the answer; prose
                       optional and non-authoritative

Measures: accuracy, wrong-answer rate, and whether the guarantee
survives each design. Pre-declared expectation: R2 improves accuracy
but forfeits certification, because a model can ignore or mangle what
is in its context; R3 keeps it. Cross-corpus comparison
(D-generic vs D-user) is reported as its own finding — domain
familiarity is a variable nobody in the arc has measured.

Non-arithmetic claim: FACTUAL answers are served under PROVENANCE
certification (source id, version, validity window, cross-source
conflict detection, staleness quarantine) rather than derivation —
the strategy specced in the V1.0 draft and deferred twice.

## 10. W7 — Two-tier certification (decision iv)

After this version an answer may depend on a model's reading, so the
external certificate splits rather than overclaims:

  TIER A — self-parsed input (the existing deterministic path).
    Unchanged and unqualified: never wrong; certified across 10,160
    trap items and 65 independent seeds; regenerable.
  TIER B — model-parsed input (the new path).
    Verified reading: every answer passed agreement, round-trip,
    consumption, scope and dimensional checks; measured wrong-rate X%
    on sealed real language; every failure itemized by class; parse
    agreement rate reported.

`certify.py` is extended to emit both tiers, to FAIL if Tier A ever
regresses, and to REFUSE to print Tier B without a current measured
wrong-rate. The one-page external certificate states both tiers and
which one a given deployment runs in.

## 11. Datasets and traffic modes (decision v)

**Primary (real language).** V1.2's sealed sets are SPENT — evaluated
once, per protocol. V1.3 draws fresh splits from the unused remainder
of the same frozen corpora (GSM8K/ASDiv/SciQ), records the
V1.2-consumed ids and asserts disjointness at generation time
[PLAN: sealed FULL 300 / UNITS 150 / THEORY 100; paired arm sample
300]. Hashes and licences already in results/real/corpus_hashes.json.

**Both traffic modes, run and compared:**
  T-repeat  3,000 draws WITH replacement from the ~1,180-item pool —
            models a repetitive production workload.
  T-unique  the ~1,180 unique items, NO replacement — the pessimistic
            case in which every query is novel.
Every traffic-dependent measurement (coverage curve, reuse curve,
acquisition yield, cost per answer) is reported for both. The gap
between them IS the measurement: it quantifies how much apparent
compounding is real recurrence versus sampling artefact.

**Secondary (product domains).** The two W6 corpora above:
hand-built, hashed, versioned, each with its own sealed split
[PLAN 100 of 300 per corpus].

## 12. Hypotheses (FROZEN)

  L1 Real traffic recurs in structure (gates W5 scope).
                                              PREDICT uncertain
  L2 Frames improve parse precision and give a reliable no-frame
     abstention signal.                       PREDICT pass
  L3 The parse/verify split lifts real-language coverage from 0% to
     materially non-zero at wrong-fire <= 2%. PREDICT pass — THE headline
  L4 The five checks catch constructed misreadings without rejecting
     good parses.                             PREDICT pass
  L5 Plan reflexes COMPOUND on T-repeat; the T-unique gap quantifies
     how much of that is sampling.            PREDICT uncertain
  L6 A cheap parser suffices: P-local within [PLAN 10pp] of P-sonnet.
                                              PREDICT uncertain — the commercial crux
  L7 R3 beats R1 on derived quantities at a lower wrong-answer rate,
     and R2 forfeits certification.           PREDICT pass
  L8 Provenance certification serves FACTUAL queries at wrong-fire
     <= 2% with staleness and conflict caught. PREDICT pass
  L9 PARITY-PLUS: zero regressions and zero wrong-fire on the legacy
     battery plus the 65-seed sweep; Tier A intact.
                                              PREDICT pass
  L10 Parse agreement is a useful confidence signal: disagreement
     concentrates on items that would otherwise be answered wrongly.
                                              PREDICT pass
  L11 Domain familiarity matters: D-user and D-generic differ
     measurably on the same query design.     PREDICT uncertain

## 13. Outcome ladder (FROZEN; priority F > D > C > B > A)

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

## 14. Deliverables

Batched bridge protocol · frame/router · parse agent · five-check
verification suite with per-check attribution · plan IR · agent
breeder · RAG arms on two corpora · provenance certification · fresh
sealed sets with hashes and a disjointness proof · both hand-built
product corpora · three recurrence curves · reuse curves for both
traffic modes · misparse-suite results · paired parse-model comparison
· two-tier certify.py and certificate · logs (invention / bug /
violation) · v1.3-final tag + snapshot + report + PDF + artifact +
memory · run_v1_3_experiment.py.
