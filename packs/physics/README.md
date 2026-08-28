# physics pack

Extracted from the reflex-poc arc @ v0.11-final (P2b-1). Loaded by
`reflex/packs/loader.py`; behavioral identity with the vendored
hardcoded+lexpatched state is verified by
`tests/test_pack_equality.py` (13 structure dumps byte-identical in
twin subprocesses) and by the E0 parity battery run with
`--engine pack`.

Contents: `kinds.json` (77 kinds: dim7, canonical unit, nouns,
aliases) · `caps.json` (58 capabilities with executor-family tags) ·
`lexicon.json` (worker noun/adjective layers, unit words, unit-index
extras, comparatives, entity nouns/adjectives, reference hypernyms,
sale verbs, ask-verb targets) · `conversions.json` (mention-level and
canonical conversion tables, B3-complete) · `breeder_struct.json`
(17 gate-certified struct patterns from the v0.11 traffic run;
authorship BREEDER; measured held-out lift zero) · `manifest.json`
(authorship + sha256).

## Engine-inline domain residue (E1 violation-log candidates)

Domain content that is NOT yet pack-driven. Each is expected to
surface in the E1 engine-freeze experiment and belongs in
`violation_log.md` when it does:

1. v4 base registry compiled members: 6 capabilities carry Python
   `pre` precondition functions defined in engine code
   (`_arc/v4/registry_v4.py`); the loader re-attaches them by taking
   the engine base registry as the union base.
2. `integrity11.certify` inner `_canon` conflict-canonicalization
   table (mass g, time min/h, speed km/h) and the chem-frame concept
   list (`molar_mass`/`solution_volume`/`dilution_factor`), plus the
   `_unit_in_span` unit-alias table — inline in the integrity engine.
3. `semparse11.parse` function-local literals: the deferred-
   comparative word tuple and the `_VERB_TGT` ask-verb map (the
   loader injects a pack copy of the latter's data for documentation,
   but the live code path reads its own literal).
4. `v9/sqr9.normalize_concept` fallback vocabulary reads the legacy
   `U9.KINDS9` table (68 kinds), which the loader intentionally does
   not touch: new-domain kinds are invisible to that fallback path.
