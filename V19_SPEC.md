# V1.9 SPEC — Reading Reflexes with Escalation Feedback (offline, gold-graded)

## Can a model's reading of a natural-language question be admitted as a reflex on the strength of agreement with an independent answer — and how often would that admit a WRONG reading?

**STATUS: FROZEN (2026-09-07) on the user's instruction "ok run it,
keep it a separate branch" — branch `v1.9-reading`, tag `v1.9-plan`.
Decisions in §11 are taken as proposed and recorded.** §7–§10 and
§11's risk rows never change after the first sealed run; amendments
are dated blocks.

Built on V0.1–V1.8. No prior version, tag, snapshot, dataset, report
or log is modified. Full arc protocol: pre-registration, hashed
sealed set, dev/sealed discipline, bugs B-numbered with superseded
runs preserved, single-command reproduction, finalize with tag +
frozen snapshot (`.env` excluded) + report + memory. Bridge only; no
API spend; the live key in `.env` is never read.

**The user's brief (2026-09-07), recorded in intent:** create a
reflex class unlike every existing one — a *reading* reflex for
natural language — backed by a feedback loop: when the engine misses
coverage and a query goes to the LLM directly, the system learns
from that escalation *if the query has a defined reflex path*.

---

## 1. What V1.8 left exactly here

Composition and reuse are closed on generator text: 1,640,387
role-aware reuse serves, zero binder wrongs, PROBE-B32 8,421/8,842 at
gold. On natural text the reach is **zero** (REAL-DIAG: 0 of 4,624
GSM8K/ASDiv/SciQ items match any skeleton; 65–82% of stated numbers
have no cue the role grammar can read). The composer's ceiling is
step grammar (99.2% of escalations are structure gaps). Every
mechanism downstream of a *reading* — gate, witness, harvest,
probation, binder — is proven; the reading is what does not exist.

The arc's record on this exact idea is the hazard list:

- **V1.0**: escalation-driven acquisition works (+5.8/+7.2pp at zero
  wrong-fire) — the loop shape is proven.
- **V1.2**: real-language acquisition loops (sonnet 98 / opus 45+
  active) gave **sealed lift zero** — the gap was composition.
- **V1.3**: plan reflexes minted from text: 7 served, 7 wrong —
  "checks verify a plan matches the TEXT, never that it answers the
  QUESTION"; corroboration cannot see interpretive error (two
  samples of one model share a reading prior).
- **V1.4**: two samples of one model give structurally different
  states ~3/4 of the time; the producing side is the hard side.
- **V1.0 K3 / V1.4**: a pure LLM answer is wrong 25–50% of the time
  on these corpora — an LLM answer is not a gold.

V1.7/V1.8 changed one thing since V1.3: a proposed plan now faces
G-P1..G-P5, an independent witness, and probation on golds, and that
stack served 1.64M reuse answers with zero wrongs. The open question
is what replaces the gold when the item is a live escalation.

---

## 2. Thesis

> A READING is a plan over the positions of a question's stated
> numbers, proposed by a model once, that the engine executes and the
> witness certifies — the model teaches the engine how to read a
> phrasing, never what the answer is. On a live escalation there is no
> gold; the only signal is AGREEMENT between the engine's execution of
> the reading and an independent model's direct answer. V1.9 measures,
> offline and against real golds, what that signal is worth: the
> false-admit rate of agreement-based admission, the reach of readings
> on natural text, and how far a reading transfers to other phrasings
> before it starts being wrong.

The feedback loop in production is then: escalate → LLM answers →
proposer emits a reading → engine executes → agreement → probation →
admitted reading serves the skeleton next time, LLM not called →
permanent shadow audit revokes on the first disagreement. V1.9 runs
the offline version of that loop where every step can be graded.

---

## 3. What is honestly unknown

**Q1 — false admission.** If the reading and the answer are wrong the
same way (shared prior, V1.3), agreement admits a wrong reflex. How
often, on real golds?

**Q2 — reach.** What fraction of GSM8K/ASDiv items yield a reading
that passes the frozen gates and executes at all? Word-numbers
("half", "dozen"), implicit constants, and irrelevant numbers all
collide with G-P4's honesty rules; the collision rate is unknown.

**Q3 — transfer.** A reading keyed on its own exact skeleton will
almost never refire on natural text (REAL-DIAG). Each abstraction of
the skeleton (names, units, stopwords) raises refire and reopens the
B32 family. Where is the curve?

**Q4 — independence.** All bridge models are one family. Is haiku
"independent enough" of sonnet to make agreement informative? A local
llama-3.1-8B answerer is the independent control if reachable.

---

## 4. Architecture

```
ITEM (natural-language question, numbers at positions p0..pk;
      gold hidden from every model)
  |
  +-- PROPOSER (bridge, sonnet; opus if time): emits a READING =
  |     a planschema17 plan whose literals are the SLOTS {n0..nk}
  |     (the question's numbers in order of appearance) plus
  |     STRUCTURAL constants; it computes nothing, states no value.
  |     Prompt shows the question with its numbers indexed; nothing
  |     else.
  |
  +-- reader19.bind: substitutes the item's own numbers into the
  |     slots -> concrete plan -> plangate18.check (G-P1..G-P4,
  |     G-P4' usage matching with bare tokens, G-P5) ->
  |     chainexec17.run (per-step + end witness) -> value v, or
  |     ABSTAIN with the gate's reason.
  |
  +-- ANSWERER (bridge, haiku; llama-3.1-8B local if reachable):
  |     answers the question directly, one number. Never sees the
  |     reading.
  |
  +-- AGREEMENT: |v - a| <= max(1e-4|a|, 1e-6)  ->  ADMIT candidate
  |
  +-- GRADING (offline only): v vs corpus gold g.
        FALSE-ADMIT = P(v != g | admitted)
        READING-CORRECT = P(v == g | executed)
        ANSWERER-CORRECT = P(a == g)   (the answerer's own quality)
  |
  +-- TRANSFER: for every executed reading, the other items whose
        skeleton matches at level L0 / L1 / L2 (see 4.2); execute the
        reading on them; correct vs gold. Refire rate and transfer
        wrong-fire per level.
```

### 4.1 The reading reflex class

`{"skeleton": <L0 skeleton of the donor>, "plan": planschema17 plan
over slots "{n<i>}", "donor": id, "proposer": model, "agree": bool,
"kind": "reading"}`. It carries no pattern regex, no roles from
roles18 (bare tokens are expected), no value. It differs from every
existing reflex in that its only content is *which stated number goes
where in which computation*. Serving = exact-skeleton match at the
frozen level + bind + full gate + witness, exactly as binder18.

### 4.2 Skeleton levels (frozen)

- **L0**: lowercase, whitespace-collapsed, every stated number → `#`
  (sign and exponent kept, as roles18).
- **L1**: L0 + capitalised tokens that are not sentence-initial → `@`
  (names), unit words canonicalised (roles18.UNIT_CANON), currency
  symbols → `$`.
- **L2**: L1 + punctuation removed, a frozen stopword list removed.

Transfer at each level is measured, never served in V1.9; the level
V1.10 may serve is the highest with zero transfer wrong-fire on
sealed.

### 4.3 Positive controls before any counting run (B24)

- Gate battery: V1.7 + V1.8 batteries still pass.
- Bind battery: a hand-written reading on a GSM8K item binds,
  executes, and matches the gold; the same reading with one slot
  index swapped is caught by G-P4' or disagrees with gold (recorded
  which).
- Agreement battery: a reading that executes to a wrong value and an
  answerer string equal to that wrong value MUST be counted as a
  false admit by the grader (the metric can go red).
- Skeleton battery: two ASDiv items known to share an L1 skeleton
  but not L0 match at L1 and not L0.

---

## 5. Datasets (frozen, hashed before any bridge call)

```
POOL     GSM8K test (1,319) + ASDiv (2,305) = 3,624 items with
         numeric golds; SciQ excluded (non-numeric).
SAMPLE   1,800 items drawn by seed 1900 from POOL, stratified 900/900
         by corpus; DEV 600 / SEALED 1,200 by hash of id.
         Golds live in a separate file the bridge never sees; batch
         files carry {id, text, numbers-indexed} only.
```

DEV is for building reader19 (bind, skeleton levels, batteries) and
reading the proposer's failure anatomy; SEALED is run once per arm
after DEV is closed. The proposer and answerer prompts are frozen
with the spec (§12).

---

## 6. Arms

| arm | proposer | answerer | n |
|---|---|---|---|
| R-sonnet/haiku | sonnet | haiku | DEV 600 + SEALED 1,200 |
| R-sonnet/llama | sonnet | llama-3.1-8B (local) | same items, only if ollama is reachable; else reported "not run" |
| R-opus/haiku | opus | haiku | SEALED only, if bridge time allows; else "not run" |

No arm serves anything; every arm grades.

---

## 7. Hypotheses (FROZEN)

| | claim | prediction |
|---|---|---|
| H1 | agreement admits wrong readings: FALSE-ADMIT > 0 on sealed | **predicted yes** (V1.3 shared prior); magnitude unknown — the version exists to measure it |
| H2 | readings reach real text: ≥30% of sealed items yield a gate-passing executable reading | uncertain; G-P4 honesty vs word-numbers and irrelevant numbers is the unknown |
| H3 | executed readings are mostly right: READING-CORRECT ≥ 80% | plausible from V1.7 plan quality (93–96%) |
| H4 | agreement filters: READING-CORRECT among admitted > among executed | predicted yes |
| H5 | L0 refire on real text ≈ 0; L1 and L2 raise refire and transfer wrong-fire together | predicted (REAL-DIAG + B32) |
| H6 | an independent-family answerer (llama) lowers FALSE-ADMIT relative to haiku at the cost of admissions | predicted, if the arm runs |

---

## 8. Metrics (FROZEN)

Primary: FALSE-ADMIT (sealed, per arm), READING-CORRECT, REACH,
ANSWERER-CORRECT, admitted count; transfer refire and wrong-fire at
L0/L1/L2. Secondary: gate-kill anatomy (which gate, why) on readings;
proposer format failures; agreement-but-abstain and
disagreement-but-correct counts; per-corpus splits.

---

## 9. Thresholds (FROZEN)

```
GATE-CTRL   all §4.3 batteries pass before counting.
SAFETY-FA   FALSE-ADMIT on sealed <= 0.5% of admitted readings for
            the primary arm; expectation: nonzero (H1).
REACH       >= 30% of sealed items executable through the gates.
QUALITY     READING-CORRECT >= 80% of executed.
FILTER      READING-CORRECT(admitted) > READING-CORRECT(executed).
TRANSFER    reported per level; a level "may serve" only at zero
            transfer wrong-fire on sealed.
SEALED-ONCE every sealed arm run once; no tuning on sealed.
```

---

## 10. Outcome ladder (FROZEN; F > E > D > C > B > A)

```
F  a GATE-CTRL battery cannot pass, or a prior version stops
   reproducing.
E  SAFETY-FA fails: agreement-based admission is unsafe as a
   production loop at this answerer; the loop needs a stronger
   signal than agreement (report the wrong-admit anatomy).
D  REACH < 10%: readings cannot be gated onto real text; the gates,
   not the models, are the wall (report the kill anatomy).
C  SAFETY-FA and REACH met but QUALITY or FILTER fails: readings are
   admissible but not good enough to serve.
B  SAFETY-FA, REACH, QUALITY, FILTER met; TRANSFER shows no level
   above L0 at zero wrong-fire (readings are one-phrasing reflexes).
A  B plus at least one level above L0 at zero transfer wrong-fire on
   sealed — readings generalise a step without breaking.
```

---

## 11. Risk register (FROZEN)

```
R1  Shared prior (V1.3): proposer and answerer agree on a wrong
    reading. Detect: FALSE-ADMIT. Mitigate: llama arm if reachable;
    nothing else in V1.9 — it is the thing measured.
R2  Gold tolerance masks wrongs: a reading that rounds differently
    counts wrong. Detect: near-miss ledger (|v-g| < 2%). Mitigate:
    reported, not tuned.
R3  G-P4 kills honest readings (word-numbers, irrelevant numbers).
    Detect: gate-kill anatomy. Mitigate: none in V1.9 (frozen gate);
    the cost is REACH.
R4  Prompt leakage: a proposer could compute the answer and hide it
    as a literal. Detect: G-P4 warrant check (non-whitelisted literal
    kills); count of such kills reported.
R5  Bridge-agent variance (V1.7 timing/format failures). Detect:
    format-failure count; one re-ask allowed, both counted.
R6  Corpus golds are themselves wrong sometimes (GSM8K has known
    errata). Detect: disagreements where haiku and reading agree
    against gold are listed for inspection, not auto-relabelled.
R7  Skeleton abstraction reopens B32. Detect: transfer wrong-fire
    per level. Mitigate: nothing served in V1.9.
R8  Answerer format noise ("$18" vs "18"). Detect: parse-failure
    count. Mitigate: a frozen numeric parser; unparsable = no
    agreement.
```

---

## 12. Decisions — taken as proposed (2026-09-07)

1. SAMPLE 1,800 (900 GSM8K + 900 ASDiv), seed 1900, DEV 600 /
   SEALED 1,200 by id hash.
2. Proposer prompt (frozen): the question with its numbers indexed
   `[n0]=48, [n1]=2, …`; asked for ONE plan in the planschema17
   schema over slots `{n0}..{nk}` and structural constants only
   (0, 1, 2, 0.5, 100, 1000, 12, 60, 7, 24, 365 — the V1.7 STRUCTURAL
   set plus calendar constants, frozen here); no arithmetic, no
   answer, no prose; `null` if the question is not a calculation.
3. Answerer prompt (frozen): the question; reply with one number
   only.
4. Agreement tolerance: max(1e-4·|a|, 1e-6).
5. Skeleton levels L0/L1/L2 as §4.2; stopword list frozen in
   reader19.
6. Arms as §6; llama arm and opus arm conditional, reported either
   way.
7. One re-ask on proposer format failure; both attempts recorded.

**Implementation note:** `tools/reader19.py` (prep / bind / score /
transfer), reusing planschema17, plangate18, chainexec17, roles18
untouched. Calendar constants extend the whitelist ONLY inside
reader19's binding step (a reading may use 12 for "dozen"); the V1.7
gate's own whitelist is not edited.

**Implementation note (2026-09-07, before any counting run):** three
reading-mode flags in `plangate18` (`STRUCTURAL_EXPR_OPTIONAL`,
`LITERAL_REUSE_OK`, `UNIT_IN_EXPR_OK`), all default False so V1.8's
gate is byte-identical, set True only inside `reader19.gate_check`:
a structural constant inside an expression needs no stated-number
token ("half" -> 0.5); a slot may be used in two steps; a unit-cued
quantity may be an arithmetic operand. Each is a relaxation that
V1.8's generator chains never needed and word-problem readings
cannot do without; their safety cost is measured by FALSE-ADMIT and
transfer wrong-fire, not assumed. The bind battery's wrong reading
(`{n0}*60/{n1}`) is caught by gold, not by any gate — the class the
agreement signal must catch in production.
