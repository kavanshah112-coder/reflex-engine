# V1.6 SPEC — The Scientific Reflex Engine

## Re-scoped: a certified calculator in front of an LLM, with a verifier on the rest

**STATUS: DRAFT v2 for review. Freezes as tag `v1.6-plan`.**
§7–§10 never change after the first sealed run. §11 lists the decisions
needed before freezing.

Built on V0.1–V1.5. No prior version, tag, snapshot, dataset, report or
log is modified.

**Draft v1 of this spec proposed a verifier-only version. The user
redirected it** (2026-09-02): accept low coverage on human/narrative
queries — at commercial scale even a modest in-domain share is a
significant saving — stop fighting the parser bottleneck, and scope the
engine solely to **scientific, arithmetic and logical reflex**, the
regime where V1.0–V1.2 already proved the design. Draft v1's verifier
evidence is preserved in §4 and becomes a component rather than the
thesis.

---

## 1. What the past three experiments taught, read together

Three versions attacked narrative language from three directions and
every one failed the same way:

| version | approach | sealed result |
|---|---|---|
| V1.3 | model parses → engine verifies | 209 certified, **1.44% wrong**; haiku 2.63% > 2% gate |
| V1.4 | open relational substrate | served **0 of 240** — safe and inert |
| V1.5 | cheap deterministic reader | 5 of 800 certified, **2 wrong = 40%** |

The bottleneck was named precisely in V1.5 §10: **composition**.
Knowing a story contains 47, 41 and 20 is not knowing the answer is
47−41+20, and guards that encode wrong compositions do not generalise
(dev 0% → sealed 40%).

Meanwhile the in-regime record never broke once:

| asset | evidence |
|---|---|
| zero wrong-fire | Tier A: **0.000 over 10,160 trap items, 65 seeds** (V1.2, formally certified) |
| in-universe coverage | V1.1 100k commercial sim: **95.5% certified, 0 wrong** |
| energy per serve | **21 mJ/certified serve** (V1.2, batch-metered; 0.85 ms/q) |
| energy per LLM call | **64.9 GPU-J** (V1.4, metered locally, positive-controlled) |
| in-regime ratio | ≈ **3,000× cheaper** per served query |

**The conclusion this version acts on:** the failures were never in the
engine's regime; they were in trying to drag narrative language *into*
that regime. V1.6 stops doing that. Narrative word problems are
declared **out of scope by design** — the engine's job on them is to
escalate, which every version since V1.2 has proven it does safely.

---

## 2. Thesis

> Deployed as a front-end for **scientific, arithmetic and logical**
> queries, the engine serves the in-domain share with certified
> zero-wrong-fire arithmetic at ~1/3,000 the energy of a model call,
> escalates everything else untouched, and a deterministic verifier
> catches a measurable fraction of LLM errors on the escalated share at
> zero cost to correct answers.

The commercial identity, continuous with V1.5's:

```
E_system ≈ (1 − s) × E_llm  +  s × E_engine        s = served share
saving   ≈ s × (1 − 0.021/64.9)  ≈  s
```

**System energy saving ≈ the served in-domain share.** Low coverage on
*human* queries is accepted: at commercial scale a workload that is 20%
in-domain saves ~20% of the whole bill, and the served answers carry a
certificate the LLM's answers never do. There is no coverage bar on
out-of-domain traffic at all — its bar is safe escalation.

---

## 3. What is honestly unknown, and is the version's core question

V1.1 closed the generator universe: parse coverage 1.0000 over a 180k
sweep, **of queries the project's own generator authored**. V1.2's
first contact with foreign text (GSM8K stories) collapsed to 519/520
abstained. Between those two points nothing has ever been measured:

> **H1. What fraction of scientific/arithmetic/logical queries phrased
> by someone else — in calculator register, not story register — does
> the engine serve?**

That number is currently unknown between roughly 0% and 95%. Every
threshold in §9 hangs on it, and it is the honest risk: "the parser
covers its own grammar" and "the parser covers the domain" are
different claims, and only the second is worth money.

The second unknown is the routing hazard, with a named precedent:
V1.2's **gsm1120** was dimensionally certified and semantically wrong —
a story problem that *looked* like physics to the gates. The re-scope
makes this the version's safety question: out-of-domain traffic must
be escalated, not certified-wrong.

---

## 4. The verifier (carried from draft v1 — evidence already collected)

The strongest form of my V1.5 "abstention pivot" was **triage**:
predict LLM failure from the packet verdict and route ahead of time.
Tested on 601 direct-LLM answers already on disk (V1.3, three models,
300 sealed items): COMPLETE 11.1% error vs 12.5% for everything else —
**lift 1.12×, no usable signal. Triage is falsified** and recorded as
such.

What survived is the post-hoc form — *"is this specific answer
wrong?"* asked after:

| check | fired | on wrong | on correct |
|---|---|---|---|
| `non_integer_count` | 5 | **5** | **0** |
| `negative` | 3 | **3** | **0** |
| `magnitude_implausible` | 16 | 4 | 12 → **excluded** |

**8 of 74 LLM errors (10.8%) caught at zero false flags across 527
correct answers** — a 1.3% retry bill. In the re-scoped architecture
this is the natural check on the **escalated share**: the engine
serves what it certifies, the LLM answers the rest, and the verifier
flags LLM answers that cannot be right.

**The admission rule (unchanged from draft v1):** a check is admitted
only if it fires zero times on correct answers in dev, is re-measured
sealed, and any check with a non-zero false-flag rate is reported and
excluded. Every check and every instrument carries a positive control
(six "green check that cannot go red" instances across V1.3–V1.4).

---

## 5. Architecture

```
QUERY
  |
  v  gateway ask()                    (V1.0, unchanged semantics)
  |
  +-- parses + certifies  ------>  SERVED, certificate attached
  |                                 (21 mJ, 0.85 ms)
  |
  +-- anything else  ---------->  ESCALATED to LLM, untouched
                                        |
                                        v
                                  VERIFIER (V1.6, reflex/verify16.py)
                                        |
                                 CLEAN --+-- FLAGGED -> retry
```

Reused without modification: the Tier A engine, gateway, packs,
`nlpw10`/packet (for verifier features only), `kindderive`,
`v5/energy.py`. New code: `reflex/verify16.py` plus its check battery,
and the S-SCI dataset builder. **No new answering machinery is built —
that is the point.**

Invariants carried forward: UNKNOWN > WRONG; no producer-supplied
value/type/operator enters certified state; Tier A untouched and
re-verified as W0.

---

## 6. Datasets

```
S-SCI-dev     400 in-domain queries, foreign-phrased (see below).
S-SCI-sealed  1,200 in-domain queries, same provenance, hashed,
              run once.
S-ROUTE       600 out-of-domain distractors: narrative word problems
              (consumed corpora are legitimate here — the only claim
              on them is ESCALATION, and their golds are irrelevant
              to it) plus gsm1120-class lookalikes.
D-answers     LLM answers on the escalated share, per model, via
              isolated bridge — the verifier's sealed material.
```

**S-SCI provenance (the contamination-critical step):** bridge models
author the *phrasings* around numerically pre-committed facts — each
item's variable values and asked-for quantity are fixed first, the
gold is computed by an **independent script (sympy/pint), never by
engine code**, and the authoring models never see the parser, grammar,
or any engine module (V1.4 B9 discipline: isolated directory, stub
filters, tokens never estimated). This breaks both circularities:
golds are not the engine grading itself, and phrasings are not the
generator's own grammar echoed back.

Domain definition, fixed before authoring: dimensional physics
computation (the 77-kind/58-capability pack), unit conversion,
arithmetic/expression evaluation, and deterministic logical evaluation.
Narrative story problems are out-of-domain by definition.

---

## 7. Hypotheses (FROZEN on freeze)

| | claim | prediction |
|---|---|---|
| V1 | the engine serves a usable fraction of foreign-phrased in-domain queries | **unknown — the core question** |
| V2 | wrong-fire on served S-SCI stays within the calculator gate (§9) | pass — the regime is Tier A's |
| V3 | S-ROUTE narrative traffic is escalated, never certified-wrong | uncertain — gsm1120 precedent |
| V4 | system energy saving ≈ served share (identity holds end-to-end, metered) | pass |
| V5 | verifier catches ≥10% of LLM errors on escalated share at zero false flags, sealed | **uncertain — V1.5's guards broke dev→sealed** |
| V6 | verifier recall holds across model scale (llama/haiku/sonnet/opus) | uncertain |
| V7 | packet verdict does not predict LLM failure | **already falsified as predictor — recorded, not re-tested** |

---

## 8. Metrics (FROZEN)

**Primary: (a) served coverage and wrong-fire on S-SCI-sealed;
(b) escalation rate on S-ROUTE; (c) verifier recall at zero false
flags on D-answers.**

Secondary: metered J/query on a mixed workload vs the identity's
prediction · per-check firing rate and precision, reported per check ·
verifier flag rate (retry bill) · served latency · coverage by domain
slice (physics / conversion / arithmetic / logic).

---

## 9. Thresholds (FROZEN)

```
SAFETY-1   wrong-fire on served S-SCI-sealed <= 0.5%.
           (A calculator wrong 2% of the time is a bad calculator;
            the historical 2% gate is demoted to a secondary report.)
SAFETY-2   zero certified answers on S-ROUTE narrative items.
           One certified-wrong routing = the gsm1120 class is open.
COVERAGE   served share of S-SCI-sealed >= 40%.
           (V1.1's 95.5% was the generator's own universe; 40% of
            foreign phrasing is the pre-registered bar for "the domain,
            not the grammar".)
ENERGY     metered mixed-workload saving within 5pp of the identity's
           prediction (all computation inside the boundary; positive
           control on the meter before any run counts).
VERIFIER   false-flag rate on sealed correct answers = 0 (a single
           false flag voids that check); recall >= 10%; flag rate
           <= 5%; every zero claim reported with its ~3/n Wilson bound.
```

---

## 10. Outcome ladder (FROZEN; priority F > E > D > C > B > A)

```
F  Tier A regressed, or V1.3/V1.4/V1.5 stop reproducing.
E  SAFETY-1 or SAFETY-2 fails: the calculator is wrong in its own
   regime, or narrative traffic gets certified.
D  safe but empty: coverage < 10% — foreign phrasing misses the
   grammar almost entirely, and the re-scope saves nothing.
C  coverage 10–40%: real but below the bar; report the measured
   commercial value honestly and stop there.
B  coverage >= 40% and safety holds, but the verifier fails its
   zero-false-flag bar sealed (system ships without it).
A  coverage >= 40%, SAFETY-1+2 hold, energy within 5pp of identity,
   verifier >= 10% recall at zero false flags on >= 2 model scales.
```

---

## 11. Open decisions — needed before freezing

1. **Coverage bar** — is 40% right for "foreign phrasing, own domain"?
   Propose 40%: below it the commercial story needs a workload
   argument the version cannot supply.
2. **Wrong-fire gate on served answers** — propose 0.5% (calculator
   standard) over the historical 2%.
3. **S-SCI authoring models** — propose haiku + sonnet via bridge,
   600 phrasings each; neither sees any engine artifact.
4. **D-answers model matrix** — propose haiku + sonnet at full
   escalated share, opus at 400, llama metered locally (the only arm
   whose energy is claimed, per B7).
5. **Verifier check budget** — the two proven checks plus the six
   draft-v1 candidates measured against the admission rule, or the two
   proven only? Propose: measure all, admit per rule.

---

## 12. What this version honestly claims, and does not

It does not claim the engine reads language — three versions proved it
does not, and this spec stops asking. It claims something narrower and
older: **within its declared scientific/arithmetic/logical domain the
engine is a certified, near-free calculator, and the version measures
how much of the honestly-phrased domain that covers** — a number the
arc has never produced, because V1.1 measured the grammar and V1.2
measured stories, and the domain lies between.

If coverage lands at 15%, the result is a 15% system energy saving
with certificates, reported as exactly that — the user's framing:
at commercial scale, a low share is still a significant number.
If it lands near zero, rung D says so and the re-scope was wrong.
Either way the question is finally the right shape: not "can the
engine do what LLMs do?" but "how much of what the engine provably
does shows up in real traffic?"
