# V1.6 SPEC — The Scientific Reflex Engine

## Re-scoped and scaled: a certified calculator with a grown, indexed reflex library, in front of an LLM, with a verifier on the rest

**STATUS: FROZEN 2026-09-02, tag `v1.6-plan` @ d098588 (user: "freeze
the spec and check previous version are freezed and then start").**
§7–§10 never change after the first sealed run. The seven §11 decisions
are RESOLVED in the AMENDMENT at the end of this file.

Built on V0.1–V1.5. No prior version, tag, snapshot, dataset, report or
log is modified. The full arc protocol applies unchanged: read
everything first, pre-register before sealed data, hash sealed sets,
dev/sealed splits, no tuning on sealed results, every bug documented
with superseded runs preserved, negatives reported prominently,
single-command reproduction, finalize with tag + frozen snapshot
(excluding `.env`) + report MD/PDF + memory update.

**Draft history (all user-directed, all pre-freeze):**
- Draft v1 proposed a verifier-only version. Evidence preserved in §4.
- Draft v2 (user redirect, 2026-09-02): accept low coverage on
  human/narrative queries, stop fighting the parser bottleneck, scope
  the engine solely to **scientific, arithmetic and logical reflex**.
- **Draft v3 (user extension, 2026-09-02): same protocol, plus —**
  (a) bridge models are **haiku, sonnet, opus and fable** (four
  scales, no others); (b) all calculation capability and every reflex
  is **hierarchically indexed** (mathematics → calculus →
  differentiation → second derivative, and so on for every domain);
  (c) the version **first builds an extensive reflex library from
  queries** before sealed evaluation; (d) the workload grows to
  **100,000 queries spanning every in-scope domain**; (e) **reflex
  creation is watched per model** — which model mints what, and how
  well its reflexes hold; (f) queries **escalate in complexity, are
  non-monotonic, and may span multiple areas** at once.

**One reversal, recorded:** draft v2 promised "no new answering
machinery." Requirement (b)+(f) reverses that at the user's direction —
advanced calculation (calculus, algebraic manipulation, multi-domain
chains) is new machinery. The reversal is paid for with a new gate
(§5.3): no symbolic result is certified without an independent numeric
cross-check, a check that carries its own positive control.

---

## 1. What the past three experiments taught, read together

Three versions attacked narrative language from three directions and
every one failed the same way:

| version | approach | sealed result |
|---|---|---|
| V1.3 | model parses → engine verifies | 209 certified, **1.44% wrong**; haiku 2.63% > 2% gate |
| V1.4 | open relational substrate | served **0 of 240** — safe and inert |
| V1.5 | cheap deterministic reader | 5 of 800 certified, **2 wrong = 40%** |

The bottleneck was named precisely in V1.5 §10: **composition** of
narrative events. Knowing a story contains 47, 41 and 20 is not knowing
the answer is 47−41+20, and guards that encode wrong compositions do
not generalise (dev 0% → sealed 40%).

Meanwhile the in-regime record never broke once:

| asset | evidence |
|---|---|
| zero wrong-fire | Tier A: **0.000 over 10,160 trap items, 65 seeds** (V1.2, formally certified) |
| in-universe coverage | V1.1 100k commercial sim: **95.5% certified, 0 wrong** |
| energy per serve | **21 mJ/certified serve** (V1.2, batch-metered; 0.85 ms/q) |
| energy per LLM call | **64.9 GPU-J** (V1.4, metered locally, positive-controlled) |
| in-regime ratio | ≈ **3,000× cheaper** per served query |
| acquisition works in-regime | V1.0: haiku +5.8pp (p 3.7e-9), sonnet +7.2pp (p≈0) sealed-residual lift @ **0.000 wrong-fire every arm**; V1.1 bridge minting opus 12 > haiku 8 > sonnet 6 |

**The conclusion this version acts on:** the failures were never in the
engine's regime; they were in dragging narrative language *into* that
regime. V1.6 stops doing that and instead does the thing the arc has
proven, at the scale and depth it has never attempted: grow, index and
certify a large reflex library over the whole scientific/arithmetic/
logical domain. Narrative word problems remain **out of scope by
design** — the engine's job on them is to escalate.

Two acquisition warnings carry forward with teeth: V1.2's acquisition
loops produced **sealed lift zero** on stories (minting cannot buy what
the regime cannot hold), and V1.1's scale inversion — **opus minted
MORE wrong reflexes than haiku** (17 vs 7) including gsm1120, a
dimensionally-certified-semantically-wrong item. Bigger minter ≠ safer
library. The gauntlet, not the model, is the safety boundary.

---

## 2. Thesis

> Deployed as a front-end for **scientific, arithmetic and logical**
> queries, the engine (i) serves the in-domain share with certified
> zero-wrong-fire computation at ~1/3,000 the energy of a model call,
> (ii) **grows that share by minting reflexes from live queries into a
> hierarchically indexed library**, safely, at four model scales,
> (iii) escalates everything else untouched, and (iv) a deterministic
> verifier catches a measurable fraction of LLM errors on the escalated
> share at zero cost to correct answers.

The commercial identity, continuous with V1.5's:

```
E_system ≈ (1 − s) × E_llm  +  s × E_engine        s = served share
saving   ≈ s × (1 − 0.021/64.9)  ≈  s
```

**System energy saving ≈ the served in-domain share — and acquisition
makes `s` a curve over traffic, not a constant.** Low coverage on
*human* queries is accepted: at commercial scale a workload that is 20%
in-domain saves ~20% of the whole bill, and the served answers carry a
certificate the LLM's answers never do. Out-of-domain traffic has no
coverage bar at all — its bar is safe escalation.

Energy constants are **reused, not re-measured**: 21 mJ/serve (V1.2)
and 64.9 GPU-J/call (V1.4) are the only metered numbers in the
identity. Per B7, nothing run through the bridge ever grounds an energy
claim, and since the user's model matrix is bridge-only (haiku, sonnet,
opus, fable), **V1.6 makes no new energy measurement** — it reports the
identity's projection from measured `s`, labelled as exactly that.

---

## 3. What is honestly unknown — the version's core questions

**Q1 — coverage under foreign phrasing (unchanged from draft v2).**
V1.1 closed the generator universe (parse 1.0000 over a 180k sweep) —
*of queries the project's own generator authored*. V1.2's first contact
with foreign text collapsed to 519/520 abstained. Between those two
points nothing has ever been measured:

> **H1. What fraction of scientific/arithmetic/logical queries phrased
> by someone else — calculator register, not story register — does the
> engine serve?** Unknown between roughly 0% and 95%.

**Q2 — does the library grow safely at depth?** The arc has only ever
minted paraphrase- and vocabulary-level reflexes over a flat capability
set. It has never minted into a **deep taxonomy** (second derivatives,
chained conversions, cross-domain compositions) and never watched
**four model scales** do it side by side — including fable, a scale
that has never touched this arc. V1.1's inversion says the risk is
real: capability-mining at higher scale minted more wrong.

**Q3 — where does complexity kill coverage?** Nothing in the arc says
whether a query needing differentiation *then* unit conversion *then*
a comparison is served, declined, or — the failure mode that matters —
certified wrong. The complexity ladder (§6.3) exists to find the depth
at which certified service honestly ends.

The routing hazard keeps its named precedent: V1.2's **gsm1120** was
dimensionally certified and semantically wrong. Out-of-domain traffic
must be escalated, not certified-wrong — at 100k scale, a 0.1% routing
leak is 100 wrong certificates.

---

## 4. The verifier (carried from draft v1 — evidence already collected)

Triage — predicting LLM failure from the packet verdict before the
call — is **falsified**: on 601 direct-LLM answers already on disk
(V1.3, three models, 300 sealed items), COMPLETE 11.1% error vs 12.5%
for everything else, lift 1.12×, no usable signal. Recorded, not
re-tested.

What survived is the post-hoc form — *"is this specific answer
wrong?"*:

| check | fired | on wrong | on correct |
|---|---|---|---|
| `non_integer_count` | 5 | **5** | **0** |
| `negative` | 3 | **3** | **0** |
| `magnitude_implausible` | 16 | 4 | 12 → **excluded** |

**8 of 74 LLM errors (10.8%) caught at zero false flags across 527
correct answers** — a 1.3% retry bill. In V1.6 this is the check on the
escalated share, now measured across all four bridge scales including
fable (H-V6).

**Admission rule (unchanged):** a check is admitted only if it fires
zero times on correct answers in dev, is re-measured sealed, and any
check with a non-zero false-flag rate is reported and excluded. Every
check and every instrument carries a positive control (six "green check
that cannot go red" instances across V1.3–V1.5).

---

## 5. Architecture

```
QUERY
  |
  v  gateway ask()                        (V1.0 semantics, unchanged)
  |
  +-- parses + certifies against the      SERVED, certificate names
  |   INDEXED REFLEX LIBRARY  --------->  value + units + taxonomy path
  |   (Tier A + minted reflexes;          (21 mJ, sub-ms)
  |    symbolic core gated by §5.3)
  |
  +-- anything else  ----------------->   ESCALATED to LLM, untouched
                                              |
                                              v
                                        VERIFIER (reflex/verify16.py)
                                              |
                                       CLEAN --+-- FLAGGED -> retry

ACQUISITION (offline, watched, per model — haiku/sonnet/opus/fable):
  residual queries -> bridge minter -> GAUNTLET (V1.0: dimensional
  gates + shadow probation, zero-wrong AND zero-lost-coverage) ->
  TAXONOMY INDEX (§5.1; unindexable = rejected) -> library
```

Reused without modification: the Tier A engine, gateway, physics pack
(77 kinds / 58 capabilities), the V1.0 acquisition gauntlet and shadow
probation, `nlpw10`/packet (verifier features only), `kindderive`,
`v5/energy.py` constants. The frozen V0.9/V0.10 namer is untouched —
Tier A depends on it (B25 discipline).

New code: `reflex/taxonomy16.py` (the index), `reflex/symcore16.py`
(the symbolic core), `reflex/acquire16.py` (the watched minting loop
over the V1.0 gauntlet), `reflex/verify16.py` (+ check battery),
`tools/build_q100k.py`, `tools/gold_independent.py`.

### 5.1 The taxonomy — every capability and every reflex has an address

A single frozen tree, `taxonomy.json`, committed **at plan freeze**,
covering the whole in-scope domain. Illustrative shape (full tree is a
freeze artifact):

```
mathematics
  arithmetic          (integer/rational ops, percentages, ratios)
  algebra             (linear/quadratic solve, rearrangement)
  calculus
    differentiation
      first_derivative
      second_derivative        <- "double differentiation"
      higher_order
      evaluate_at_point
    integration
      indefinite | definite
    limits
  trigonometry · sequences_series · number_theory
  combinatorics_probability · statistics
physics
  (the 77-kind pack mapped node-by-node: kinematics, dynamics,
   energy_power, electricity, waves, thermal, ...)
chemistry_quantitative   (stoichiometry, molarity, gas laws)
units_conversion         (length/mass/time/compound/currency-free)
logic
  propositional_evaluation · set_operations · boolean_algebra
```

Rules, all hard:
- **Every existing capability is mapped to exactly one node** before
  any run (the mapping is a freeze artifact; unmappable capability =
  spec bug, fixed pre-freeze).
- **Every minted reflex must be indexed to a leaf** by evidence the
  gauntlet can check (the dimensional signature and operator set of the
  reflex, not the minter's say-so — B25: the namer's claim is never
  trusted). **A reflex the index cannot place is rejected**, whatever
  its probation record. UNKNOWN > WRONG applies to addresses too.
- **Every certificate names its taxonomy path(s).** A served answer
  that cannot name its path is a bug of class SAFETY-1.
- Multi-area queries carry multiple paths (one per chain step).

The index is what turns 100k results into a map: coverage, wrong-fire
and library growth are all reported **per node and per depth** (§8).

### 5.2 The library build — "extensive library of reflex from query"

Phase L (library), before any sealed evaluation, mirrors V1.0/V1.1
acquisition but at taxonomy scale and **watched**:

1. Stream the acquisition split of Q-100K (§6.2) through the gateway.
2. Residuals (escalated in-domain items) are batched **per taxonomy
   node** and offered to each minting model separately — haiku,
   sonnet, opus, fable — through the isolated bridge (V1.4 B9
   discipline: minters see query text only; never parser, grammar,
   engine module, or each other's candidates).
3. Every candidate reflex runs the **V1.0 gauntlet unchanged**:
   dimensional capability gates, then shadow probation requiring
   **zero-wrong AND zero-lost-coverage**, then §5.1 indexing.
4. **Everything is logged per model**: offered / proposed / gate-killed
   / probation-killed / index-killed / admitted, with the node, the
   probation transcript, and every rejected candidate preserved. This
   log IS deliverable (e) — reflex creation, watched.

The four model libraries are kept **separate through evaluation**
(arms M-h, M-s, M-o, M-f) plus a merged arm M-all (union, gauntlet
re-run on the union to catch conflicts). No minted reflex ever
modifies Tier A; the library is additive and each reflex is
individually revocable.

### 5.3 The symbolic core — new machinery, new gate

`symcore16` executes the advanced-calculation nodes (calculus, algebra,
series, ...) deterministically (sympy-backed). Because golds are also
computed symbolically (§6.4), engine and gold could share a substrate
and silently share a bug. The pre-registered break for that
circularity:

> **NUMERIC CROSS-CHECK GATE.** Every symbolic result is verified by
> independent numeric code (`gold_independent.py`, mpmath, no sympy
> import) before certification: derivatives/integrals checked by
> finite-difference / quadrature agreement at k=7 random sample points
> within declared tolerance; algebraic solutions checked by
> substitution. A result failing the cross-check is **escalated, never
> served**. The gate carries a positive control — a battery of
> deliberately wrong symbolic results that MUST all fail — run before
> any counting run (B24 discipline: instruments get positive controls).

### 5.4 Invariants carried forward

UNKNOWN > WRONG; no producer-supplied value/type/operator enters
certified state (minted reflexes propose *procedures*, and every
procedure's output is engine-computed and §5.3-checked); the LLM never
overrides a deterministic gate; Tier A untouched and re-verified as W0;
bridge isolation absolute (B9); tokens_in/out never estimated (B7).

---

## 6. Datasets

```
taxonomy.json      the frozen tree + capability mapping (§5.1).
Q-100K             100,000 in-scope queries + routed distractors,
                   labelled (taxonomy paths, depth, monotonicity,
                   register), hashed at freeze. Splits in §6.2.
S-SCI-dev          400 foreign-phrased in-domain queries (dev).
S-SCI-sealed       2,000 foreign-phrased in-domain queries, hashed,
                   run once. THE H1 measurement.
S-ROUTE            600 out-of-domain distractors: narrative word
                   problems (consumed corpora legitimate — the only
                   claim on them is ESCALATION) + gsm1120-class
                   lookalikes.
D-answers          LLM answers on sampled escalated share, per model
                   (haiku/sonnet/opus/fable), isolated bridge — the
                   verifier's sealed material.
```

### 6.1 What 100,000 queries honestly means

100k items cannot all be human-authored, and pretending otherwise would
re-commit V1.1's sin of measuring the grammar and calling it the
domain. The composition is therefore **labelled by register and the
claims are separated**:

- **~97k programmatic**: built by `build_q100k.py` compositionally over
  the taxonomy — this measures *domain and depth* coverage of the
  library, labelled "own-register" wherever generator phrasing is used.
- **~3k bridge-authored foreign phrasings** distributed across nodes
  and depths (same anti-contamination rules as S-SCI), overlaid so the
  register axis exists *inside* Q-100K too.
- **S-SCI-sealed remains the only source of the headline H1
  foreign-phrasing coverage number.** Q-100K's own-register numbers are
  never quoted as human coverage. This separation is frozen.

Engine cost at this scale is trivial (0.85 ms/q → minutes); bridge cost
is controlled by sampling (§6.5).

### 6.2 Q-100K splits (frozen at freeze, by hash)

```
ACQ    60,000   acquisition stream — Phase L mints from its residuals
DEV    10,000   development measurement, unrestricted use
SEAL   30,000   sealed at freeze, run ONCE per arm after Phase L ends
```

Distractors (out-of-domain narrative, ~5% of each split) flow through
all three so routing is measured in-stream, not only on S-ROUTE.

### 6.3 The complexity ladder — "complicated, non-monotonic, multi-area"

Every item carries two frozen labels:

- **depth** = number of chained certified steps required.
  d1 single node ("differentiate x³·sin x") · d2 chain within a domain
  ("second derivative, then evaluate at x=2") · d3 cross-domain chain
  ("differentiate the position law, convert m/s to km/h") · d4+ long
  chains with a logical comparison on top.
- **non-monotonic flag** = consecutive steps use *different* operations
  or direction reversals (the V1.5 failure shape, now in-regime where
  the composition IS deterministically derivable).

Frozen mix per split: **d1 40% · d2 30% · d3 20% · d4+ 10%; ≥50% of
d2+ non-monotonic; ≥25% of d3+ multi-area (≥2 top-level domains).**
Coverage and wrong-fire are reported **per depth rung** — the decay
curve is a primary deliverable, not a footnote.

### 6.4 Gold provenance (the contamination-critical step)

Every gold is computed by `gold_independent.py` (sympy/pint for
construction + the mpmath numeric layer as the independent witness),
**never by engine code**, and stored with the item at freeze. For
symbolic items the stored gold includes the numeric-witness values, so
grading never runs sympy at evaluation time. Foreign phrasings are
authored by bridge models around **numerically pre-committed facts**;
authoring models never see parser, grammar, or any engine module, and
never see each other. This breaks both circularities: golds are not the
engine grading itself, and phrasings are not the generator's grammar
echoed back.

### 6.5 Bridge budgets (frozen; bridge = agents, no API spend)

```
minting        per model: residual batches to a cap of 1,500 offers
verifier       D-answers: 400 sealed escalated items per model
S-SCI author   authoring split across haiku/sonnet/opus/fable equally
               (each phrasing tagged with its author; no model is
                evaluated on phrasings it authored — frozen rule)
```

---

## 7. Hypotheses (FROZEN on freeze)

| | claim | prediction |
|---|---|---|
| V1 | the engine + grown library serves a usable fraction of foreign-phrased in-domain queries (S-SCI-sealed) | **unknown — the core question** |
| V2 | wrong-fire on all served answers stays within SAFETY-1 | pass — the regime is Tier A's, but §5.3 machinery is new |
| V3 | out-of-domain traffic (S-ROUTE + in-stream distractors) is escalated, never certified | uncertain — gsm1120 precedent, now at 100k scale |
| V4 | Phase L acquisition lifts sealed coverage over the Tier-A-only baseline at ≥1 model scale, at 0.000 minted wrong-fire | uncertain — V1.0 says yes in-regime, V1.2 says minting can't exceed the regime |
| V5 | minting quality is NOT monotone in model scale (fable/opus mint more but not more safely than haiku/sonnet) | **predicted from V1.1's inversion — now testable at 4 scales** |
| V6 | verifier catches ≥10% of LLM errors on the escalated share at zero false flags, sealed, per model | uncertain — V1.5's guards broke dev→sealed |
| V7 | coverage decays with depth but wrong-fire does NOT (the engine declines what it cannot chain, rather than guessing) | the arc's whole safety claim, now at depth |
| V8 | multi-area (cross-domain) items are served at a meaningful fraction of same-depth single-domain items | unknown |
| V9 | the numeric cross-check gate catches every seeded wrong symbolic result (positive control) and blocks real ones at a measurable rate | must pass its control or no symbolic serve counts |
| V10 | packet verdict does not predict LLM failure | **already falsified — recorded, not re-tested** |

---

## 8. Metrics (FROZEN)

**Primary: (a) served coverage + wrong-fire on S-SCI-sealed (H1);
(b) served coverage + wrong-fire on Q-100K SEAL, per depth rung and
per taxonomy node, per arm (baseline / M-h / M-s / M-o / M-f / M-all);
(c) escalation rate on S-ROUTE and in-stream distractors;
(d) acquisition ledger per model: offered → proposed → gate-killed →
probation-killed → index-killed → admitted, plus sealed lift and
minted-reflex wrong-fire; (e) verifier recall at zero false flags on
D-answers, per model.**

Secondary: taxonomy coverage map (served share per node — the
library's shape); depth-decay curves per arm; non-monotonic vs
monotonic served share at equal depth; identity-projected energy
saving from measured `s` (labelled projection, no new measurement);
per-check verifier firing/precision; served latency at library scale
(does a 10×+ larger library slow the 0.85 ms serve?); flag rate.

---

## 9. Thresholds (FROZEN)

```
SAFETY-1     wrong-fire on ALL served answers (every arm, every set)
             <= 0.5%. A certificate that cannot name its taxonomy
             path counts as a wrong-fire.
SAFETY-2     zero certified answers on S-ROUTE / in-stream narrative
             distractors. One = the gsm1120 class is open.
SAFETY-3     minted reflexes: 0.000 wrong-fire attributable to any
             admitted reflex on sealed data (V1.0's standard). A
             single wrong answer traced to a minted reflex revokes
             it AND is reported; >=3 from one model's library fails
             that arm.
GATE-CTRL    the §5.3 positive-control battery (seeded wrong
             symbolic results) passes 100% before any counting run;
             a control failure voids all symbolic serves until fixed
             and rerun (B24).
COVERAGE     served share of S-SCI-sealed >= 40% (H1 headline).
             Q-100K SEAL own-register coverage is reported but has
             no bar — it is the map, not the claim.
ACQ-LIFT     M-all sealed coverage minus baseline >= +5pp on Q-100K
             SEAL with SAFETY-3 intact, else acquisition is reported
             as not paying at taxonomy depth.
VERIFIER     false-flag rate on sealed correct answers = 0 (one
             false flag voids that check); recall >= 10%; flag rate
             <= 5%; zero claims carry ~3/n Wilson bounds.
```

The historical 2% wrong-fire gate is demoted to a secondary report.

---

## 10. Outcome ladder (FROZEN; priority F > E > D > C > B > A)

```
F  Tier A regressed, or V1.3/V1.4/V1.5 stop reproducing, or
   GATE-CTRL cannot be made to pass.
E  SAFETY-1, SAFETY-2 or SAFETY-3 fails: the calculator is wrong in
   its own regime, narrative traffic gets certified, or the minted
   library is unsafe.
D  safe but empty: S-SCI-sealed coverage < 10% — foreign phrasing
   misses the engine almost entirely and the re-scope saves nothing.
C  S-SCI coverage 10–40%: real but below bar; report the measured
   commercial value honestly and stop there.
B  coverage >= 40% and all safety holds, but EITHER acquisition
   fails ACQ-LIFT (the library does not grow at depth) OR the
   verifier fails its zero-false-flag bar sealed. Ship what held.
A  coverage >= 40%; SAFETY-1/2/3 hold across all four arms;
   ACQ-LIFT met with the per-model creation ledger complete;
   depth curve reported through d4+; verifier >= 10% recall at
   zero false flags on >= 2 of the 4 model scales.
```

---

## 11. Open decisions — needed before freezing

1. **Coverage bar** — 40% on S-SCI-sealed foreign phrasing. Confirm.
2. **Wrong-fire gate** — 0.5% on served (calculator standard). Confirm.
3. **Taxonomy granularity** — freeze the tree at ~3–4 levels deep,
   ~120–180 leaves (proposed). Deeper splits after freeze are
   reporting views only, never new admission targets.
4. **Q-100K splits and mix** — 60k/10k/30k, depth mix 40/30/20/10,
   ~5% distractors, ~3k foreign overlay. Confirm.
5. **Minting cap** — 1,500 offers per model (6,000 bridge minting
   tasks total). Confirm, or set the cap you want to spend.
6. **Verifier battery** — the two proven checks plus the six draft-v1
   candidates, measured against the admission rule. Confirm.
7. **Fable in the matrix** — fable runs via the bridge like the
   others; it is also the scale this session runs on. Minting and
   D-answers isolation (B9) apply to it identically. Confirm.

---

## 12. What this version honestly claims, and does not

It does not claim the engine reads language — three versions proved it
does not, and this spec stops asking. It claims something narrower and
now much larger: **within its declared scientific/arithmetic/logical
domain, the engine is a certified near-free calculator whose capability
library can be grown from traffic and indexed to an address, and this
version measures — at 100k scale, four model scales, and four depth
rungs — how much of the honestly-phrased domain that covers, how safely
the library grows, and where complexity ends it.**

---

## AMENDMENT — §11 decisions RESOLVED at freeze (2026-09-02)

Resolved at the user's freeze instruction; recorded before any V1.6
code ran on data.

1. **Coverage bar: 40%** on S-SCI-sealed, as proposed.
2. **Wrong-fire gate: 0.5%** on served answers, as proposed; the 2%
   historical gate is a secondary report.
3. **Taxonomy granularity: the tree is frozen at 47 leaves** (2–4
   levels; committed `taxonomy.json`, generator
   `tools/gen_taxonomy16.py --check` verifies byte-stability), leaner
   than the ~120–180 sketch because every leaf must be separately
   reportable at Q-100K scale. 20 leaves are Tier A-executed, 27 are
   symcore16-executed. All 58 existing capabilities map to Tier A
   leaves only (asserted by the generator). Deeper splits after freeze
   are reporting views, never admission targets.
4. **Q-100K: 60k ACQ / 10k DEV / 30k SEAL**, depth mix 40/30/20/10,
   ~5% narrative distractors per split, ~3k foreign-phrased overlay,
   as proposed.
5. **Minting cap: 1,500 offers per model** (haiku, sonnet, opus,
   fable), as proposed.
6. **Verifier battery: the 2 proven checks + the 6 draft-v1
   candidates**, each against the zero-false-flag admission rule.
7. **Model matrix: haiku, sonnet, opus, fable via isolated bridge —
   and no local model anywhere.** User direction (2026-09-02): "in
   this exp we are not using ollama, only sonnet haiku opus and
   fable." Consequences, frozen: no new energy measurement exists in
   V1.6 (B7 — bridge tokens never ground energy claims); the energy
   number is the identity's projection from measured `s` using the
   V1.2/V1.4 metered constants, labelled as a projection; the two
   ollama-adapter tests are recorded N/A in W0_V16.md, not modified.

Process rule added by W0 (recorded in W0_V16.md): sealed V1.6 datasets
are committed with `.gitattributes -text` and hashed over raw bytes,
closing the CRLF ambiguity found while re-verifying V1.5's seal.

The numbers keep their registers separate: Q-100K's own-register
coverage is the *map* of what the library can do; S-SCI-sealed's
foreign-phrasing coverage is the *claim* about human traffic; and the
identity converts the claim into the energy story. If foreign coverage
lands at 15%, the result is a 15% projected system saving with
certificates, reported as exactly that. If acquisition mints nothing
admissible at depth, ACQ-LIFT says so in one line. If the fourth rung
of the ladder is empty, the depth curve says where the honest edge of
certified calculation currently sits — which is, either way, a number
this arc has never had.
