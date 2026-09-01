# V1.5 PLAN — Cheap Semantic Worker + Selective LLM Escalation

**STATUS: DRAFT for review. Freezes as tag `v1.5-plan`.**
§9–§13 never change after the first sealed run. §14 lists what needs
your decision before freezing.

Built on V0.1–V1.4. No prior version, tag, snapshot, dataset, report or
log is modified. V1.3 and V1.4 remain reproducible and are re-verified
as W0 acceptance.

---

## 1. What already exists (inspected before designing)

The brief asks for an NLP worker, an information packet, a relational
substrate, a Path Manager and a breeder. **Four of the five are already
built.** V1.5 is mostly wiring and measurement, not construction.

| brief asks for | already exists | where |
|---|---|---|
| §1 cheap NLP worker | **YES** — 640 LOC deterministic pipeline | `v10/nlpw10.py` |
| §2 information packet | **YES** — the worker's output matrix | `nlpw10.parse()` |
| §3 relational substrate | **YES ×2** — V1.4 open substrate, V0.11 fact state | `reflex/rss.py`, `v11/semstate11.py` |
| §4 semantic indexing | partial — entity graph exists | `v11/semstate11.py` |
| §5 unknown engine | **YES** — typed status per quantity | `nlpw10` status field |
| §8 Path Manager | **YES** — goal regression, no depth limit | `v10/planner10.py`, `v10/pathman10.py` |
| §19 breeder | **YES** — pollution-resistant, gated | `reflex/acquire.py` |
| §13 energy meter | **YES** — GPU L2 telemetry + CPU L3 model | `v5/energy.py` |

`nlpw10.parse()` already returns exactly the §2 packet: entities with
spans; quantities carrying value, unit, concept, role, polarity,
`time_context`, `source_span`, `provenance`, `confidence` and a typed
`status`; a target; and ambiguity flags. It computes nothing and never
emits a derived value.

§5's KNOWN / UNKNOWN / AMBIGUOUS already exist as
`status ∈ {ok, unknown_concept, ambiguous_concept}`.

**V1.5 therefore reuses and measures rather than rebuilds.** What is
genuinely new: the packet→substrate index (§4), selective escalation
with a typed handoff contract (§6, §7), the amortization store (§14 of
the brief), and the whole-system energy accounting.

---

## 2. The measurement that sets the version's economics

Run before writing this plan, on 400 items of the **sealed** S3
real-language set, deterministic, no model:

```
PACKET COMPLETE  (target known AND every quantity named)    8.2%
target known                                               32.0%
all quantities named                                       19.0%
mean worker time                                       6.39 ms/query
```

Against V1.4's measured pure-LLM baseline on the same hardware
(64.9 GPU-J/query, 76.4 J/correct, 51/60 correct), the worker costs
roughly **0.3 J** — about **0.5%** of one LLM call.

### 2.1 The energy identity, and what it implies

Because the worker is essentially free relative to a model call:

```
E_v15  ≈  f_escalate × E_llm  +  E_worker  +  E_engine
       ≈  f_escalate × E_llm                (E_worker+E_engine ≈ 0.5%)

saving ≈  1 − f_escalate  =  deterministic coverage
```

**Energy saving is, to within half a percent, just the fraction of
queries answered without calling the model.** Break-even is not a query
count — it is immediate and trivial, at any deterministic coverage
above ~0.5%. The interesting quantity is not *whether* there is a
saving but *how large*, and that equals coverage.

At today's measured 8.2% packet-completeness the ceiling is an **8%
energy saving**, and only if every one of those is answered correctly.

### 2.2 A consequence the brief does not anticipate — flagged before freezing

The brief's §6 reasons that escalating "the smallest unresolved unit"
is cheaper than escalating the whole query. **On this baseline that is
close to false, and it matters enough to state up front.**

The pure-LLM baseline already asks for a bare number at
`max_tokens = 24`. It is not an expensive reasoning call; it is the
cheapest possible call. A typed single-step escalation sends a
comparable or larger prompt and asks for a comparable output, so it
costs roughly the same as simply asking the question.

**Selective escalation therefore saves energy by NOT CALLING, not by
calling more cheaply.** Delegating a smaller unit is valuable for
*safety and typing* — the LLM never authors the final answer — but it
should not be expected to reduce per-call cost.

This is pre-registered as a measurement (M4, §10) rather than assumed
in either direction: V1.5 will measure escalation cost against
full-query cost directly, and if partial escalation *is* materially
cheaper, that is a finding worth having.

---

## 3. Architecture

```
QUERY
  |
  v  nlpw10.parse()                    ~6.4 ms, no model
INFORMATION PACKET  (entities, quantities, units, roles,
                     polarity, temporal, target, spans,
                     provenance, typed status)
  |
  v  packet_index (NEW)
RELATIONAL SUBSTRATE   reflex/rss.py nodes+relations,
                       entity identity preserved
  |
  v  planner10 / pathman10 goal regression (no depth limit)
PATH
  |
  +-- every step has a capability  -->  REFLEX  (deterministic)
  |
  +-- a step is UNKNOWN            -->  TYPED ESCALATION (NEW)
                                          smallest unresolved unit
                                          typed handoff contract
                                          engine evaluates, LLM never
                                          authors the answer
  |
  v
VALIDATOR (integrity + applicability + check 8 + provenance)
  |
  v
CERTIFIED  |  ESCALATED  |  ABSTAINED
```

Invariants carried forward unchanged:

- **UNKNOWN > WRONG.** Unproven state abstains or escalates.
- No producer-supplied value, type, or operator enters certified state.
- The LLM never overrides a deterministic gate.
- Tier A stays untouched and re-verified.

---

## 4. New components

**`reflex/packet.py`** — normalises `nlpw10.parse()` output into the
V1.5 packet and computes a typed completeness verdict:
`COMPLETE | MISSING_TARGET | MISSING_CONCEPT | AMBIGUOUS | CONFLICTING`.

**`reflex/packet_index.py`** — indexes a packet into `rss.State`
preserving entity identity, relation direction, scope, temporal order,
span, value, unit, dimension, dependency and target. Must distinguish
the brief's four cases (§4): *has 5 apples* / *gives 5 to Sarah* /
*Sarah gives John 5* / *had 5 before giving 2*.

**`reflex/escalate.py`** — the typed handoff contract (§7): step id,
input ids and types, operation, output type, source spans,
assumptions, uncertainty, provenance. The receiving reflex rejects
wrong type, wrong unit, wrong dimension, invalid provenance, malformed
expression, incompatible entity, incompatible path position,
unsupported operation.

**`reflex/pstore.py`** — the amortization store: exact and structural
packet reuse, gated by the V1.4 semantic-signature rule
(`similarity ≠ applicability`) so paraphrases share and different
stories never merge.

---

## 5. Datasets

All sealed and hashed before evaluation; none inspected answer-side
first.

| | set | size | provenance |
|---|---|---|---|
| **S3** | real language | 1,200 | V1.4, unchanged, disjointness already proved |
| **S1** | adversarial semantic | 600 | V1.4, unchanged |
| **S6** | tiered real language T1–T10 | 1,000 | NEW, from the 674 unused corpus items + generated T9/T10 |
| **S7** | repeated/structural workload | 2,000 | NEW, for amortization |
| **S8** | adversarial safety (§17) | 400 | NEW, incl. injection and false-provenance |

**Corpus constraint, stated now:** the real-language pool holds 3,568
items; V1.3 consumed ~1,780 and V1.4's S3 took 1,200, leaving **674
fresh**. S6 is therefore 674 real + 326 generated for the tiers real
text cannot supply (T9 theoretical, T10 out-of-distribution), and this
is a limit of the corpus, not a design choice.

---

## 6. Model matrix (§12, §22 — required)

| model | pure | +worker | +substrate | +path mgr | full V1.5 |
|---|---|---|---|---|---|
| llama-8B (local, metered) | ✓ | ✓ | ✓ | ✓ | ✓ |
| haiku (bridge) | ✓ | ✓ | ✓ | ✓ | ✓ |
| sonnet (bridge) | ✓ | ✓ | ✓ | ✓ | ✓ |
| **opus (bridge) — as a SERVING model, not a breeder** | ✓ | ✓ | ✓ | ✓ | ✓ |

**Energy is measured only on the local llama arm.** Bridge arms report
calls, tokens, coverage and wrong-fire — never joules (V1.3 B7:
servicing agents fabricated token counts, and one reverse-engineered
another's invented formula). Bridge arms are serviced from a directory
containing no engine module (V1.3 B9).

**Manager transfer (§24):** substrate built by opus, operated by
sonnet / haiku / llama managers, against same-model builder+manager.

---

## 7. Ablations (§21)

```
A0  pure LLM                       A6  full V1.5
A1  reflex only                    A7  full minus relational structure
A2  NLP worker only                A8  LLM builds the full packet
A3  NLP + substrate                A9  forced full-query escalation
A4  NLP + substrate + path mgr     A10 full, no packet reuse
A5  NLP + substrate + selective    A11 full, with packet reuse
```

A9 and A0 differ only in who assembles the prompt; if they cost the
same, §2.2 is confirmed.

---

## 8. Energy accounting (§13, §26 — binding)

**Primary metric: TOTAL END-TO-END ENERGY PER CORRECT ANSWER.**

Inside the boundary, without exception: NLP worker · packet
construction · indexing · substrate lookup · Path Manager · every LLM
escalation · validation · reflex execution.

The deterministic engine's marginal energy is reported **separately and
never substituted** for the whole-system figure. V1.2's 21 mJ/serve and
V1.4's 19.9× disadvantage are the same system measured with the model
outside and inside the boundary respectively; only the second answers a
commercial question.

Reported separately: cold-start · steady-state · marginal · amortized.

**Instrument discipline (V1.4 B24):** the first V1.4 energy run
reported 0.0 J on every channel because a `_Window` was read inside its
own block. Every energy run now carries a **positive control** that
voids the run if all channels read zero.

---

## 9. Hypotheses (FROZEN on freeze)

| | claim | prediction |
|---|---|---|
| H1 | the cheap worker builds useful packets for a substantial fraction of real language | **uncertain — measured at 8.2% complete today** |
| H2 | relational substrate beats a flat representation on state integrity | pass (V1.4 measured 100% vs 10%) |
| H3 | selective escalation costs less than full-query reasoning | **doubt — see §2.2** |
| H4 | typed handoffs preserve the safety advantage | pass |
| H5 | packet reuse amortizes interpretation | uncertain |
| H6 | a small manager can operate a large-model substrate | uncertain |
| H7 | opus benefits economically from reflexes | **doubt — opus is strong standalone and the saving is capped by coverage** |
| H8 | the advantage grows with complexity / repetition | uncertain |
| H9 | explicit UNKNOWN reduces wrong-fire without destroying coverage | pass on safety, **doubt on coverage** (V1.4: coverage went to zero) |
| H10 | the Path Manager composes reflex→reflex→LLM→reflex correctly | uncertain |
| H11 | relational structure generalises better than fixed labels | uncertain |
| H12 | end-to-end J/correct beats pure LLM with the safety gate intact | **uncertain — ceiling is 8% at today's coverage** |

---

## 10. Primary and secondary metrics (FROZEN)

**M1 (primary)** end-to-end J per correct answer, local metered arm.
**M2** deterministic coverage — the fraction answered with zero LLM calls.
**M3** wrong-fire, per arm, per tier, with Wilson intervals.
**M4** escalation cost vs full-query cost (tests §2.2 directly).
**M5** cumulative energy vs query count, cold and repeated.
**M6** LLM calls/query, tokens/query, reflex fraction.
**M7** packet completeness by tier T1–T10.
**M8** manager-transfer accuracy and wrong-fire delta.

---

## 11. Thresholds (FROZEN — no post-hoc changes)

```
SAFETY     wrong-fire <= 2% per sealed arm, 0 preferred.
           A claim of "<=2%" requires the Wilson UPPER bound < 2%.
COVERAGE   deterministic coverage >= 15% of real language.
           (Today 8.2%. Below 15%, the energy ceiling is not
            commercially interesting.)
ENERGY     end-to-end J/correct at least 20% below pure LLM on the
           metered arm. Requires ~20% deterministic coverage, by §2.1.
AMORT      a break-even query count reported if one exists; per §2.1 it
           is expected to be trivial, which is itself a finding.
POWER      no wrong-fire gate claim without the Wilson upper bound.
```

---

## 12. Outcome ladder (FROZEN; priority F > E > D > C > B > A)

```
F  no pre-registered outcome met, or Tier A regressed, or V1.3/V1.4
   no longer reproduce.
E  safety or semantic integrity fails: wrong-fire above 2% on any
   sealed arm.
D  semantic acquisition remains too expensive: deterministic coverage
   below the 15% threshold, so the energy ceiling stays uninteresting.
C  reflex improves economics for small models but not for opus.
B  the energy advantage exists only after amortization/repetition.
A  end-to-end J/correct at least 20% below pure LLM, wrong-fire within
   threshold, coverage above threshold, on the metered arm.
```

---

## 13. Discipline (carried forward, non-negotiable)

Sealed sets hashed before evaluation · deterministic seeds · dev/sealed
split for any debugging · superseded runs preserved under
`superseded_<tag>/` · no tuning on sealed results · every bug logged
with when it entered and what it cost · affected measurements re-run ·
all prior tags and snapshots untouched · single-command reproduction.

**Every detector and every instrument needs a positive control** — a
case it MUST fire on, running beside the case it must not. Six
instances in two versions of a green check that could not go red
(V1.3 B8, B16; V1.4 B19, B20, B22, B24).

**Negatives preserved and explicitly re-tested, not buried** (§30):
V1.4's 0/240 real-language serving · model-generated relational
disagreement at ~75% · the 19.9× GPU energy disadvantage · earlier
parser and generalization failures · LLM-routing nulls · breeder
pollution findings.

---

## 14. Open decisions — needed before freezing

1. **Coverage threshold.** 15% is set against a measured 8.2%. It
   demands roughly a doubling. Too aggressive, about right, or should
   V1.5 pre-register a *lower* bar and treat coverage improvement as
   the whole experiment?
2. **Where the coverage must come from.** The worker's misses are
   68% unknown target and 81% partly-unnamed quantities — mostly
   everyday nouns absent from the 77-kind physics pack. Extending the
   kind lexicon from **non-sealed** traffic is the obvious lever and it
   is the same move that produced V1.4's B18. Approve, or hold the
   lexicon fixed and let coverage be what it is?
3. **Bridge scale.** Four models × twelve ablations × sealed sets is
   far beyond V1.4's ~20 servicing agents. Propose: full matrix on the
   metered llama arm, and A0/A5/A6 only on the three bridge models.
4. **S6/S7/S8 sizes**, given only 674 fresh real items remain.
5. **§2.2.** If escalation is not cheaper per call, the brief's central
   mechanism reduces to "avoid calls". Confirm that reading before it
   is frozen into the hypotheses.

---

## 15. The question V1.5 answers

> Can a cheap deterministic worker plus a relational substrate answer
> enough natural language **without a model call** to lower total
> end-to-end energy per correct answer — while keeping the safety gate?

By §2.1 that reduces to one number: **deterministic coverage**. Today it
is 8.2%. V1.5 is the experiment that finds out whether it can be moved,
and what it costs in safety to move it.
