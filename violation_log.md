# Violation log — engine-freeze accounting (V1_SPEC §4)

## Amendments to the frozen engine (post-parity, pre-data; parity
re-verified green after each)

1. **Acquired-kind target recovery** (reflex/engine.py): the vendored
   target-namer cannot see single-word nouns of kinds added after
   pack load (its multiword-phrase rule plus import-frozen v9
   fallback tables). Recovery scans the ask for acquired-kind nouns,
   fires ONLY when acquired kinds exist — base-pack behavior
   untouched by construction. Discovered via the loop-close demo.
2. **Wrong-target override** (same file): when the base namer targets
   a kind whose value is already a given input (the arc's
   "asking-for-what-you-were-told" suspicion signal) and an acquired
   kind's noun literally appears in the ask, the acquired kind wins.
   Same acquired-kinds guard.

## Standing engine-inline domain residue (E1/V1.1 candidates; from
packs/physics/README.md, plus what EXP-ACQ measured)

- v4 base registry compiled members (`pre` functions).
- integrity11 inner `_canon` table, chem-frame list, unit-alias table.
- semparse11 function-local literals (deferred-comparative tuple,
  `_VERB_TGT` ask-verb map).
- v9 normalize_concept fallback vocabulary (legacy 68-kind table).
- **Measured to matter** (residual diagnosis + arm results): word-
  number vocabulary gaps ("a dozen"), hyphenated unit forms
  ("2-tonne"), ask-focus scoring. These, not domain mappings, are
  the bulk of the sealed residual — the V1.1 engine worklist.
