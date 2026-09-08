# V1.10 SPEC — DRAFT v1 for review (not frozen)

## Suggest, don't serve: a 400k-query workload from plain arithmetic to complex physics, four one-model arms, with the library proposing readings and the escalation's own answer deciding — and the token bill measured

Branch `v1.10-suggest` from `v1.9-reading` @ b9c7199 (post-hoc probe
committed). Nothing here is frozen; §11 lists the decisions the spec
needs before freeze.

---

## 1. What V1.9 and its post-hoc probe left exactly here

1. **One model can read its own escalations.** Readings admitted under
   A2 (engine gates + agreement with the model's own answer) are wrong
   by gold 0.5–1.4% and genuinely wrong 0–0.12% across sonnet, opus,
   haiku, fable (SEALED 1,764, run once). One genuine on the primary
   arm made the letter E.
2. **The lexical gates bought nothing on the large arms.** G-P6 +
   S-INT/RATIO/PCT/GEOM removed 0/12, 0/13, 1/12 of the by-gold wrongs
   on sonnet/opus/fable and cost 13–17% of admissions; they removed
   12/19 on haiku. The filter that works is the own answer (V8).
3. **Served on its own authority, cue-keyed reuse is unsafe**: 13–58
   wrong of 35–76 would-serves (V6). **Suggested and filtered by the own
   answer, it works**: 612–688 of 1,764 sealed items served from other
   items' readings at 3–8 wrong by gold, 0 new genuine (V10, post-hoc,
   never served). The four hazards the probe named: zero-slot items
   served by constant plans; multi-answer asks the proposer had declined
   ("how much did each"); value-right/reading-wrong hits (6–19% of
   reuse hits compute the answer by a different plan); and the whole
   result being post-hoc on a set that is now burned.
4. **Burned data.** V1.9's 1,764 SEALED and S1's 1,800 were used for the
   post-hoc probe; they can never be sealed again. GSM8K-test and ASDiv
   are exhausted as sealed material. V1.10 needs fresh gold.
5. **Scale still costs the bridge.** V1.9 moved ~14k model outputs
   (readings + answers, 4 arms) in about a day of agents. 400k queries ×
   4 arms cannot all touch a model. The design must put the model on a
   hashed sample and the engine on everything.

---

## 2. Thesis

A reading, once admitted, is a reflex the **binder may suggest** for any
later query with the same cue key; the engine executes every suggestion
and the escalation's own answer — which production computes anyway —
decides. This turns the one-phrasing reflex of V1.9 into a transferable
one at zero extra model cost, and the model's token bill on a workload
falls in proportion to what the library can suggest. On a 400k workload
that climbs from one-step arithmetic in plain language to multi-domain
physics chains and complex word problems, this version measures: (a)
how safety holds per tier, (b) how far suggestion reaches per tier,
(c) what the model costs in tokens per query with the engine in front
versus alone, and (d) whether the engine abstains cleanly on questions
it cannot compute (physics concepts).

**Invariants (unchanged):** UNKNOWN > WRONG; models propose structure,
engines compute; independent witness on every served value; positive
controls for every detector and instrument; frozen ladder; sealed sets
hashed and run once; every by-gold wrong published and classified;
golds never relabelled; no second model in any arm; no local model; no
API spend outside the bridge; the proposer never sees golds, engine or
code.

---

## 3. What is honestly unknown

- **U1** Does the own-answer filter hold at ~1% by gold and ~0 genuine
  when the library is 10× larger and candidates per item run into the
  thousands? (More candidates = more chances for a coincidental plan
  to reproduce a wrong own answer.)
- **U2** Does suggestion transfer *across tiers* — readings minted on
  simple items serving complex ones and vice versa — or only within?
- **U3** Does the physics chain machinery of V1.7/V1.8 (role skeletons,
  93–96% certified at zero wrong on generator chains) survive physics
  *word problems* in natural language, where the reading has to find
  the chain?
- **U4** How much of the token bill does the engine actually remove?
  V1.6-style coverage (55%) predicts roughly half; complex tiers will
  pull it down.
- **U5** Can a suggested reading ever be served *without* the model
  (key-consensus, §4.6) at zero wrong? V6 says no for single readings;
  consensus of every admitted reading on the key is untested.
- **U6** Do concept questions (no computable ask) ever get certified?
  Every such certification is a wrong-fire by definition.

---

## 4. Architecture (one model per arm; engine identical across arms)

### 4.1 Gateway path (V1.9 stack + SUGGEST)

```
query ──► reader (NUM19, roles18, ask type, cue key, S-MULTI, zero-slot flag)
      ──► exact library (packs, V1.8 role skeletons, exact reading skeletons)
              │ hit ──► bind ──► gates ──► execute ──► witness ──► CERTIFIED
      ──► SUGGEST: every admitted reading on the cue key (impure keys allowed)
              │ each: bind ──► gates ──► execute ──► value_i
      ──► ESCALATE: model answers (production does this anyway)
      ──► ADMIT if some value_i agrees with the own answer (A2 on reuse)
              │ ──► serve value; record (item, donor, plan signature)
      ──► else ESCALATED answer served as LLM_ESCALATED (uncertified)
      ──► acquisition: on a hashed fraction, model also PROPOSES a reading
              │ ──► A2 ──► library (probation)
```

### 4.2 Admission rules (all reported; A2S is the version's rule)

| rule | meaning |
|---|---|
| A2 | fresh reading, gates + own-answer agreement (V1.9) |
| A2S | suggested reading, gates + own-answer agreement |
| A0S | suggested reading, own-answer agreement only (reported, never the rule) |
| KC | key-consensus: every admitted reading on the key executes on the item and ALL agree — served without the model **in shadow only** (§4.6) |

### 4.3 New engine rules (set on DEV before any sealed run)

- **Z-SLOT** a candidate reading with zero number slots is never
  suggested (a constant is not a computation). V10: P0 served 80–104
  such items per arm.
- **S-MULTI** the ask names two quantities ("how much did each", "how
  long are the pieces", "find the ages of X and Y", "N and M
  respectively", "cases plus extra") → abstain from both fresh and
  suggested admission. V10: removed every new wrong (a1460, a1477,
  a1481, a2268, a1409); false-abstention rate measured on DEV, bar <3%.
- **G-P6 demoted to REPORTED on sonnet/opus/fable; kept as a RULE on
  haiku only** (V8: it removed nothing on the large arms and 12/19 on
  haiku). Both variants are scored on every arm; the per-arm rule is
  fixed at freeze from V1.9 DEV, not tuned on V1.10 data.
- **PLAN-AGREEMENT minting.** A suggested hit is *served* on value
  agreement, but it *mints* (adds the item as a donor of that reading)
  only if the plan's bound signature equals the signature of a fresh
  A2 reading of the same item or of ≥1 other admitted donor on the
  key (two-donor rule of V1.8). V10: 6–19% of hits were value-right,
  reading-wrong.
- **Physics chain readings.** For P-tier items the reading language is
  the V1.7 plan DAG over pack kinds (`chainexec17`), not bare
  arithmetic: the proposer names kinds and roles, the engine supplies
  formulas (G-P5 certified formulas only). Bare-arithmetic readings on
  physics items are gate-killed (dimensionless plan on a dimensioned
  ask = G-P1).

### 4.4 Cue key (frozen as V1.9: ask type | number count | roles18 cues)

Kept deliberately impure: suggestion is a *proposal*, not a serve, so
purity is no longer a precondition. CUE-PURITY and candidates-per-item
are reported per tier.

### 4.5 Model roles (both by the SAME model in every arm)

- **Answerer** — answers the escalated query directly, one number (or,
  for PC items, one letter / "cannot compute"). Its usage is the token
  bill.
- **Proposer** — on the hashed acquisition fraction, emits a reading
  (`{"plan": …}` or null), same protocol as V1.9.
- **Author** — for tiers T4 and P4 only (§5): writes a word problem
  around a plan + values handed to it. Authoring is *data
  construction*, not an engine role; an author never authors items its
  own arm is sealed on (V1.7 rule).

### 4.6 Key-consensus serving (measured in shadow, never served)

For each escalated item, if ≥3 admitted readings exist on its key and
ALL execute to the same value (tolerance as V1.9), the engine records a
KC serve and grades it by gold. KC-WRONG = 0 on SEALED across all arms
is the only condition under which a later version may serve natural-
language readings without the model. This is U5 made testable.

### 4.7 Instruments

- **Tokens.** Every bridge agent's harness-reported usage
  (`subagent_tokens`, never the agent's self-report — B7) is logged per
  batch with its item count and role. TOKENS/QUERY per (arm, tier,
  role) = batch usage ÷ items. Text-token estimate (chars/4 of question
  + answer) is reported beside it so the harness overhead is visible.
  Positive control: a batch of 25 empty-answer items must report a
  non-zero, smaller usage than a real batch (an instrument that cannot
  read zero-vs-nonzero is not an instrument — B24).
- **Energy.** meter18 on the engine side, per certified serve and per
  suggestion executed (the suggestion path executes ~200 candidates
  per item; its cost must be measured, not assumed).
- **Timing.** Engine latency per item per path (exact, suggest,
  escalate) on the 400k pass.

---

## 5. Datasets (frozen and hashed before any bridge call)

### 5.1 The 400k workload W-400K — tiers, sources, gold provenance

| tier | content | n | source | gold |
|---|---|---|---|---|
| T1 | one-step arithmetic, plain language ("Ann has 5 apples and buys 3 more…") | 80,000 | generator (build_q100k narrative templates, seed 11010) | by construction |
| T2 | two/three-step word problems, simple language, ASDiv-like | 80,000 | generator, composition-first (V1.7 DAG generator restricted to arithmetic leaves, 2–3 steps) | witness |
| T3 | real multi-step word problems | 7,473 | **GSM8K train** (never used in the arc; needs download, §11) | corpus |
| T3′ | real variants with structural perturbations | 1,000 | **SVAMP** (needs download, §11) | corpus |
| T4 | complex word problems: 4–6 steps, multi-entity, distractor sentences, word numbers, mixed units | 20,000 | **plan-first authoring** by bridge authors round-robin over the four models; gold = engine value of the handed plan; QC: an independent answer by a *different* model must agree at authoring, else the item is DEV-only | engine + QC |
| P1 | physics, single formula, 77 pack kinds | 80,000 | V1.6 generator | pack witness |
| P2 | physics chains k=3, multi-domain | 60,000 | V1.7 generator | chain witness |
| P3 | physics chains k=5–6, ≥2 domains, unit conversions, non-monotonic step order — "highly complex" | 40,000 | V1.7 generator, high stratum | chain witness |
| P4 | highly complex physics *word problems*: P3 plans authored as narratives (plan-first, as T4) | 10,000 | bridge authors + QC | engine + QC |
| PC | physics **concept** questions, multiple choice, no computable ask | 1,000 | **SciQ test** (in `corpora/sciq.zip`) | corpus |
| D | narrative distractors (no answer exists) | 2% overlay | V1.7 distractor pool | escalation-only |
| **total** | | **≈ 400k** | | |

Complexity is thus a *ladder in two dimensions*: computational depth
(T1 → T2 → T3 → T4; P1 → P2 → P3) and linguistic distance from the
generator (generator → real corpus → authored). Every metric is
reported per tier and per arm.

### 5.2 Splits (by id hash, frozen)

```
ACQ    40%  — the stream the loop learns on (readings minted here)
DEV    10%  — rules and thresholds set here (Z-SLOT, S-MULTI, G-P6 per arm)
SEAL   25%  — scored once per arm
REPLAY 25%  — evaluated once at the end with the final library, never tuned on
```
Real corpora (T3, T3′, PC) are split by the same hash; authored tiers
(T4, P4) additionally never place an item in SEAL/REPLAY for the arm
whose model authored it. V1.9's 1,764 + S1's 1,800 (burned) enter ACQ
only, tagged `burned`, and never count toward any sealed number.

### 5.3 The model-in-the-loop sample (what the bridge actually touches)

The engine runs on all 400k. The model runs on **E-SAMPLE**: a hashed
sample of escalations per arm — the proposal is **4,000 answers + 4,000
readings per arm in ACQ, 3,000 answers per arm in SEAL, 1,000 in
REPLAY**, stratified by tier (≥250 per tier per phase, PC and T3′ in
full). Token and safety numbers on SEAL are *measured* on the sample
and *extrapolated* to the workload by the engine-measured escalation
rate; the report shows both numbers and the extrapolation explicitly.
Estimated bridge load: ~2.3× V1.9 per arm for answers/readings plus
~30k authored items with QC — roughly two days of agents at 20
concurrent. If this is too much, §11 gives the cut order.

### 5.4 Provenance rules

Golds live only under `results/v110/data/`; agents receive batch files
of `{id, text, numbers}` (and, for authors, `{plan, values}`) and never
golds, engine or code. SciQ and GSM8K-train files are hashed at
freeze. Authored items carry `author_model`; QC disagreement rate is
reported as a dataset-quality number, and QC-rejected items are DEV
only.

---

## 6. Arms

| arm | model (answers, proposes, authors) | notes |
|---|---|---|
| **M-sonnet** (primary) | sonnet | ladder read here |
| M-opus | opus | highest reading quality in V1.9 (98.4%) |
| M-haiku | haiku | scale question; G-P6 stays a rule here |
| M-fable | fable | |

Engine and library start identical; libraries diverge as each arm
mints from its own ACQ stream. A **D-arm** (deterministic, no model, no
minting) runs the 400k for the exact-library baseline and the energy
floor.

---

## 7. Hypotheses (to freeze)

| | claim | prediction |
|---|---|---|
| H1 | A2S (suggested + own answer) on SEAL is wrong by gold ≤ fresh A2's rate on every arm | predicted (V10: 0.47–1.16% vs 0.86–1.39%) |
| H2 | GENUINE wrong under A2S = 0 on M-sonnet SEAL | the crux; V10 says yes, V1.9 says one item can break it |
| H3 | Z-SLOT + S-MULTI remove every V10-class new wrong and cost < 3% false abstention on DEV | predicted |
| H4 | SUGGEST-REACH (share of escalated SEAL items served by suggestion) ≥ 30% on T1–T3, falling with tier; T4 and P4 < 15% | predicted |
| H5 | Physics chains P1–P3 certified ≥ 90% at zero wrong via role skeletons (V1.7/V1.8 machinery), model-free | predicted (V1.7: 93–96%) |
| H6 | P4 (physics word problems): fresh reading reach < 50%, and every P4 wrong traces to reading, never to formula (G-P5) | predicted |
| H7 | PC concept items: 0 certified on every arm; escalation 100% | predicted; any certification = SAFETY-PC failure |
| H8 | TOKENS/QUERY with the engine in front ≤ 50% of LLM-only on W-400K overall, and > 80% on T4/P4 | predicted from coverage |
| H9 | KC (key consensus) serves > 0 items on SEAL with KC-WRONG > 0 | predicted — consensus of impure keys is still impure |
| H10 | scale monotone: haiku ≥ sonnet in genuine wrongs, ≤ in suggest-reach | predicted |
| H11 | value-right/reading-wrong hits are 5–20% of A2S serves and PLAN-AGREEMENT minting excludes all of them from the library | predicted (V10: 6–19%) |
| H12 | the acquisition curve (SUGGEST-REACH vs ACQ position, checkpoints every 20k) is concave and non-flat — unlike V0.11's flat 25k curve | uncertain |

---

## 8. Metrics (to freeze)

Per arm × tier × phase: certified (exact), A2 fresh, A2S, A0S, KC-shadow;
wrong by gold with post-hoc class (gold errata / format / rounding /
unit / convention / multi-answer / GENUINE); GENUINE count; reach per
path; escalation rate; candidates per item; plan-agreement share;
library size and donors per reading; Z-SLOT/S-MULTI/G-P6 kill and
false-abstention rates on DEV; TOKENS/QUERY by role with LLM-only
baseline; energy per certified serve and per suggestion; latency per
path; PC certified count; authored-item QC disagreement rate;
acquisition curve.

---

## 9. Thresholds (to freeze)

```
GATE-CTRL    every battery passes (V1.9 controls + Z-SLOT + S-MULTI +
             token instrument positive control + PC control: a numeric
             item disguised as MC must still be certified, a concept
             item must never be).
SAFETY-GEN   GENUINE wrongs under A2S on M-sonnet SEAL = 0.
SAFETY-FA    A2S wrong by gold on SEAL ≤ 1.0% per arm (corpus errata
             floor observed ~0.4%).
SAFETY-PC    PC items certified = 0 on every arm.
SAFETY-CHAIN P1–P3 model-free certified wrong = 0 (V1.8 standard).
REACH-S      SUGGEST-REACH on SEAL real tiers (T3, T3′) ≥ 30% per arm.
REACH-P4     reported, no bar.
RULES        Z-SLOT, S-MULTI false abstention < 3% each on DEV.
TOKENS       engine-in-front TOKENS/QUERY ≤ 50% of LLM-only on W-400K
             (extrapolated) and the measured-sample number published
             beside it.
KC-SAFE      KC-WRONG = 0 on SEAL (all arms) for key-consensus serving
             to be declared testable live in a later version.
SEALED-ONCE  SEAL and REPLAY: engine pass, bridge sample and score,
             once per arm.
```

---

## 10. Outcome ladder (to freeze; F > E > D > C > B > A)

```
F  a control fails, or V1.9 numbers stop reproducing on the burned set.
E  SAFETY-GEN fails, or SAFETY-PC fails, or SAFETY-CHAIN fails.
D  safety holds but REACH-S < 30%: suggestion is safe and does not
   transfer at scale.
C  safety and reach hold but SAFETY-FA fails on non-genuine classes:
   safe in truth, wrong by the corpus; or TOKENS fails.
B  all bars hold; KC measured; KC-WRONG > 0 or KC-SERVED = 0: the
   library transfers through the model's own answer, and cannot yet
   serve natural language on its own.
A  B plus KC-WRONG = 0 with KC-SERVED > 0 on SEAL for every arm.
```

---

## 11. Decisions needed before freeze

1. **Downloads** (need your OK — the harness treats file downloads as
   permission-gated): GSM8K train (`grade-school-math` repo, ~4 MB
   JSONL) and SVAMP (~1 MB JSON). Without them T3 has no fresh real
   gold and the real-language sealed layer is PC + authored only.
2. **Bridge budget.** Proposed 8k model outputs per arm in ACQ + 3k
   SEAL + 1k REPLAY + ~30k authored/QC items. Cut order if too much:
   REPLAY sample → P4 authoring 10k→4k → T4 20k→8k → ACQ readings 4k→2k.
3. **Authored tiers.** Plan-first authoring uses a model to write the
   story and a different model to QC the gold. This is dataset
   construction, not the engine; confirm you accept model-written items
   in SEAL for tiers T4/P4 (never authored by the sealed arm).
4. **SAFETY-FA bar.** V1.9 measured 0.5–1.4% by gold with ~0.4% errata
   floor; the draft says 1.0%. Alternative: report genuine only and
   drop the by-gold bar to C-only.
5. **G-P6 per arm** as proposed (rule on haiku, reported elsewhere)?
   Or keep it a rule everywhere and pay 13–17% reach.
6. **Physics reading language.** Proposers on P4 must name pack kinds;
   this needs the kind list in the batch file (77 names, no formulas).
   Confirm that is not "seeing the engine".
7. **Sample stratification** — ≥250 per tier per phase, PC in full.

---

## 12. What this version would claim, and would not

Claim: the first workload-scale (400k) measurement of a self-learning
reflex library on natural language across a complexity ladder, with
safety per tier, transfer via suggestion, the token bill of a model
behind an engine versus alone, model-free certification of complex
physics chains, and honest abstention on non-computable physics
questions — all four scales, one model per arm. Not claim: that
suggested readings can be served without the model (KC is shadow-only
and predicted to fail), that authored items are as clean as corpus
items (QC rate published), or that the extrapolated token number is a
measurement (the sample number is; the extrapolation is arithmetic on
the measured escalation rate).

---

## AMENDMENT — §11 decisions RESOLVED at freeze (2026-09-08, user: "freeze n continue with proposed decisions, ok for downloads")

1. Downloads approved: GSM8K train and SVAMP fetched at freeze, hashed in `results/v110/data/HASHES.json`.
2. Bridge budget as proposed (8k/3k/1k per arm; ~30k authored + QC); cut order as written if throughput forces it, each cut logged in the ledger.
3. Authored tiers T4/P4 accepted in SEAL/REPLAY, never authored by the sealed arm, QC by a different model, QC-rejected → DEV only.
4. SAFETY-FA ≤ 1.0% by gold per arm; GENUINE published separately.
5. G-P6: rule on M-haiku, reported on M-sonnet/M-opus/M-fable.
6. Pack kind names (77) may appear in physics batch files; formulas never.
7. Sample stratification ≥250 per tier per phase, PC and T3′ in full.

§7–§10 are FROZEN with this amendment. Tag `v1.10-plan`.
