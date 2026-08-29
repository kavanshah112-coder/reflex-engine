# -*- coding: utf-8 -*-
# origin: new for V1.1 — W1 engine-layer fixes (V1_1_SPEC §1)
"""Deterministic engine-layer patches. _arc stays byte-frozen; these
apply at the wrapper layer only.

F1 word-number vocabulary  — query pre-normalization (dozen, half,
   couple-of, N-and-a-half). Fires only on matching phrases, so
   non-matching queries are byte-identical inputs (parity-safe).
F2 hyphenated number-unit  — "2-tonne" -> "2 tonne"
   (digit-hyphen-letter only; digit-hyphen-digit untouched).
F3 ask-focus retry         — implemented in reflex/engine.py as a
   retry-AFTER-abstain with an alternative target (kind-noun in the
   ask, or a pack target-verb). Only abstentions are retried, and
   only for coverage-type abstain reasons, so no answered item can
   ever change (parity-plus safe by construction).
"""
import re

# ---- F1: word-number phrases -> digits (longest patterns first)
_WORD_VAL = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
             "eleven": 11, "twelve": 12}
_F1_SUBS = [
    (re.compile(r"\bhalf\s+a\s+dozen\b", re.I), "6"),
    (re.compile(r"\btwo\s+dozen\b", re.I), "24"),
    (re.compile(r"\ba\s+dozen\b", re.I), "12"),
    (re.compile(r"\bdozens?\b", re.I), None),   # bare 'dozen(s)' —
    #   no numeral claim; left untouched (None = skip)
    (re.compile(r"\ba\s+couple\s+of\b", re.I), "2"),
    (re.compile(r"\bhalf\s+(?:a|an|of\s+a|of\s+an)\b", re.I), "0.5"),
    (re.compile(r"\ba\s+quarter\s+of\s+(?:a|an)\b", re.I), "0.25"),
]
_F1_AND_A_HALF = re.compile(
    r"\b(\d+(?:\.\d+)?|" + "|".join(_WORD_VAL) +
    r")\s+and\s+a\s+half\b", re.I)

# ---- F2: digit-hyphen-letter separation
_F2_RE = re.compile(r"(\d)-([A-Za-z])")

# F7 (W1b): height-cue adjectives the arc's miners kept rediscovering
PATCH_ADJ = {"winched": "height", "up": "height"}


# F1e: MULTI-WORD verbal numbers -> digits ("Nine hundred" -> 900).
# Single-word numbers stay on the vendored path (it handles them,
# and converting bare "one" would mint spurious mentions). Needed
# because partial normalization (a dozen->12) otherwise mixes digits
# into verbal spans, breaking the integrity span check's
# verbal-number tolerance.
_NUMWORD = ("zero|one|two|three|four|five|six|seven|eight|nine|ten|"
            "eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
            "seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|"
            "sixty|seventy|eighty|ninety|hundred|thousand|million")
_F1_MULTI = re.compile(
    rf"\b(?:{_NUMWORD})(?:[\s-](?:{_NUMWORD}|and))+\b", re.I)

# ---- W1b (Amendment B): the last measured residual families
# F5: money-prefixed WORD numbers ("$twelve each") — the digit path
# handles $ prefixes; the word-number path never did
_F5_MONEYWORD = re.compile(
    rf"\$\s?((?:{_NUMWORD})(?:[\s-](?:{_NUMWORD}|and))*)\b", re.I)
# F6: dimension lists ("2 by 1 by 0.1 metres") -> explicit
# length/width/height phrasing the parser's adjective machinery knows
_F6_DIMS = re.compile(
    r"\b(\d+(?:\.\d+)?)\s+by\s+(\d+(?:\.\d+)?)\s+by\s+"
    r"(\d+(?:\.\d+)?)\s*(metres|meters|metre|meter|m|cm|mm)\b",
    re.I)


def _words_to_number(phrase):
    import sys
    from pathlib import Path
    arc = Path(__file__).resolve().parent / "_arc"
    if str(arc) not in sys.path:
        sys.path.insert(0, str(arc))
    from v9.sqr9 import words_to_number
    return words_to_number(phrase)


def normalize_query(q):
    """Apply F1+F2. Returns (normalized, changed?)."""
    out = q

    def _multi(m):
        t = m.group(0).lower().replace("-", " ")
        t = t.replace(" and ", " ")
        v = _words_to_number(t)
        if v is None:
            return m.group(0)
        return f"{v:g}"
    def _moneyword(m):
        t = m.group(1).lower().replace("-", " ").replace(" and ",
                                                        " ")
        v = _words_to_number(t)
        return m.group(0) if v is None else f"${v:g}"
    out = _F5_MONEYWORD.sub(_moneyword, out)

    def _dims(m):
        # spelled metre forms use the short unit: the legacy index
        # maps "metres" uniquely to height (v0.11-inherited state,
        # kept for parity), while "m" is multi-candidate and lets the
        # long/wide/high adjectives resolve each dimension
        u = m.group(4).lower()
        u = "m" if u.startswith("met") else u
        return (f"{m.group(1)} {u} long, {m.group(2)} {u} wide, "
                f"{m.group(3)} {u} high")
    out = _F6_DIMS.sub(_dims, out)
    out = _F1_MULTI.sub(_multi, out)
    for rx, rep in _F1_SUBS:
        if rep is None:
            continue
        out = rx.sub(rep, out)

    def _aah(m):
        tok = m.group(1).lower()
        v = _WORD_VAL.get(tok)
        if v is None:
            try:
                v = float(tok)
            except ValueError:
                return m.group(0)
        return f"{v + 0.5:g}"
    out = _F1_AND_A_HALF.sub(_aah, out)
    out = _F2_RE.sub(r"\1 \2", out)
    return out, out != q


# ---- F4: lexicon patches surfaced by F1-F3 testing (violation_log)
# F4b: unit words the vendored table lacks (capture gate)
# + V1.2 W1.2 audit findings: index keys the capture path could
# never produce (noun-path-alive, capture-dead)
PATCH_UNIT_WORDS = {"tonne", "tonnes", "widgets", "widget",
                    "kph", "coulombs"}
# intentionally-dead unit-index aliases (documented audit
# exceptions): 'c'/'k' are single-letter ambiguity hazards;
# months/years/yr/customers have index kinds NARROWER than the
# token's real usage (months -> cust_lifetime only), so capture
# would hijack phrase-scoped naming that is currently correct —
# the phrase path stays authoritative for them (measured: enlivening
# 'months' broke cplx10 chains before the battery caught it)
AUDIT_DEAD_UNIT_KEYS = {"c", "k", "months", "years", "yr",
                        "customers"}
# F4b/F4d: unit-index entries — tonne mass forms + spelled-out rate
# compounds that _unit_after builds ("metres per second" ->
# "metres/second") but the index never contained
PATCH_UNIT_INDEX = {
    "tonne": ["mass"], "tonnes": ["mass"],
    "metres/second": ["speed"], "meters/second": ["speed"],
    "metre/second": ["speed"], "meter/second": ["speed"],
    "kilometres/hour": ["speed"], "kilometers/hour": ["speed"],
    "km/hour": ["speed"],
}
# F4b: canonical conversion for the newly capturable tonne forms is
# already in the pack table (mass t/tonne/tonnes * 1000)


# F4e: caret-exponent unit capture ("2 m^3" — the vendored UNIT_RE
# stops at '^', truncating to "m"). Wrapper prefers a full
# caret/compound form WHEN the index knows it; otherwise verbatim
# original behavior.
_CARET_RE = re.compile(
    r"^\s*([A-Za-z]+(?:\^\d)?(?:/[A-Za-z]+(?:\^\d)?)?)")


def apply_lexicon_patches(W, unit_extras):
    """Called by the loader after pack injection (engine-layer,
    single auditable site)."""
    W.UNIT_WORDS.update(PATCH_UNIT_WORDS)
    for u, ks in PATCH_UNIT_INDEX.items():
        W._UNIT_IDX.setdefault(u, list(ks))
        unit_extras.setdefault(u, list(ks))
    for a, k in PATCH_ADJ.items():
        W._ADJ.setdefault(a, k)
    if not getattr(W._unit_after, "_v11_caret", False):
        _orig = W._unit_after

        def _unit_after_caret(text, end):
            m = _CARET_RE.match(text[end:end + 24])
            if m and "^" in m.group(1):
                u = m.group(1).strip().rstrip(".,;:!?")
                if u.lower() in W._UNIT_IDX:
                    return u
            return _orig(text, end)

        _unit_after_caret._v11_caret = True
        W._unit_after = _unit_after_caret


# W1.1 (V1.2) guard scope: the ambiguity guard fires only when the
# ask CONTAINS a reference-shaped expression that failed to resolve
# ("the tenth one", "that unit", "the other one", "in question") —
# single-scenario chains with incidental entities and kind-only asks
# stay global (the cplx battery is the arbiter). Residual exposure:
# novel reference forms outside this detector (violation_log).
ASK_REF_RE = re.compile(
    r"\bthe\s+[a-z]+\s+one\b|\bthat\s+[a-z]+\b|\bthe\s+other\b|"
    r"\bin\s+question\b", re.I)


# ---- F3 support: alternative-target candidates from the ask clause
_RETRYABLE = {"no_target", "no_plan", "empty_state_or_target"}


def alt_targets(query, current_target, kinds, target_verbs,
                input_concepts):
    """Deterministic alternative targets for the post-abstain retry.
    Returns an ordered, deduplicated list (at most 2)."""
    segs = [s for s in re.split(r"[.?!]", query) if s.strip()]
    askl = (segs[-1] if segs else query).lower()
    toks = re.findall(r"[a-z_]+", askl)
    tokset = set(toks)
    out = []
    # (a) unique kind noun in the ask that is NOT the current target;
    #     single-word nouns included (the vendored namer's blind spot)
    hits = set()
    for k in kinds:
        if k == current_target:
            continue
        spec = kinds[k]     # __getitem__, so _KindsView merges the
        #                     worker's extra nouns ("joules" etc.)
        nouns = [k] + [n.lower() for n in (spec[2] or [])]
        for n in nouns:
            if (" " in n and n in askl) or n in tokset:
                hits.add(k)
                break
    if len(hits) == 1:
        out.append(next(iter(hits)))
    # (b) pack target-verb hit (first match in ask order)
    for w in toks:
        k = (target_verbs or {}).get(w)
        if k and k in kinds and k != current_target and k not in out:
            out.append(k)
            break
    return out[:2]
