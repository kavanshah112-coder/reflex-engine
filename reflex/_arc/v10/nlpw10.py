# -*- coding: utf-8 -*-
"""V0.10 NLP Worker (spec Sections 4-6): a DETERMINISTIC linguistic
pipeline converting natural language into the typed matrix. No model
call, no answer computation, no hidden answers, no invented
quantities. Emits an SQR-compatible dict EXTENDED with v10 fields
(clause, polarity, time_context, confidence, status, unknowns) so the
V0.9 validator/compiler and all V0.9 comparisons run unchanged.

Pipeline:
  1. clause segmentation (sentences + strong separators)
  2. numeric mention extraction (digits, decimals, thousands commas,
     word-numbers, percentages, money)
  3. unit capture (token window after the number; $-prefix)
  4. concept naming via the frozen V0.9 alias/dimension machinery
     (normalize_concept path 2-4: noun-phrase, token vote, dimension)
  5. entity segmentation (clause-subject heuristic)
  6. role/polarity/time cues per clause + local window
  7. target recovery from the ask clause
  8. unknown/ambiguity budget accounting (typed conditions, not a
     scalar confidence)

Every quantity carries a VERBATIM source span. provenance=USER_TEXT
for extracted values; the worker never emits DERIVED values.
"""
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v9.sqr9 import (words_to_number, normalize_concept,  # noqa: E402
                     _NUM_RE)
from v9.universe9 import KINDS9 as _K9                    # noqa: E402

# ---- worker vocabulary layer: EXTENDS the frozen V0.9 kind nouns
# with surface forms the deterministic worker needs. The frozen
# structures are never mutated; this is the worker's own lexicon.
_EXTRA_NOUNS = {
    "data_count": ["measurements", "samples", "probes", "trials",
                   "observations"],
    "dilution_factor": ["fold", "thinned", "diluted", "factor"],
    "energy": ["joules"],
    "time": ["operates", "stays on", "runs"],
    "fixed_cost": ["flat", "fixed charge", "flat charge",
                   "fixed fee", "fixed costs"],
    "count": ["housings", "brackets", "panels", "turns out",
              "becomes"],
    "capex": ["upfront investment", "investment"],
    "batches_month": ["batches per month"],
    "months_count": ["months of operation"],
    "payback_months": ["pay back", "pays back", "payback"],
}


class _KindsView(dict):
    """KINDS9-shaped view whose noun lists include _EXTRA_NOUNS."""
    def __getitem__(self, k):
        spec = dict.__getitem__(self, k)
        if k in _EXTRA_NOUNS:
            return (spec[0], spec[1],
                    list(spec[2] or []) + _EXTRA_NOUNS[k]) + \
                tuple(spec[3:])
        return spec


def _load_kinds():
    try:
        from v10.universe10 import KINDS10
        return _KindsView(KINDS10)
    except Exception:
        return _KindsView(_K9)


KINDS9 = _load_kinds()

# ------------------------------------------------------ role cue lexicons
CUES = {
    "historical": r"\b(was|were|used to|old|previous(?:ly)?|originally|"
                  r"last (?:year|month|week|quarter)|before the|"
                  r"formerly|at first|initially)\b",
    "hypothetical": r"\b(if|would|suppose|supposing|imagine|were to|"
                    r"in case|hypothetically|could)\b",
    "example": r"\b(for example|for instance|e\.g\.|such as|"
               r"like when|as an example)\b",
    "negated": r"\b(not|no longer|"
               r"without (?!a break|a stop|a pause|rest)|"
               r"except|excluding|isn'?t|"
               r"doesn'?t|won'?t|never|neither)\b",
    "future": r"\b(will|next (?:year|month|week|quarter)|planned|"
              r"upcoming|projected)\b",
    "spec_rating": r"\b(rated|rating|nameplate|label(?:led|ed)?\s+"
                   r"(?:at|says)|capacity of|can (?:hold|carry|"
                   r"handle)|up to|at most|maximum of|shelf holds|"
                   r"unused|spare|leftover|in stock|warehouse|"
                   r"rival|competitor|another (?:shop|firm|vendor)|"
                   r"visitors|night shift|manual|quotes|quoted|"
                   r"top speed|spec(?:ification| sheet)|brochure|"
                   r"datasheet)\b",
}
CUR_RE = re.compile(r"\b(now|today|currently|current|this (?:year|"
                    r"month|week)|new)\b", re.I)
CUE_RE = {k: re.compile(v, re.I) for k, v in CUES.items()}
QUOTE_RE = re.compile(r'["“”]')

SPLIT_RE = re.compile(
    r"(?<=[.?!;])\s+|,\s+(?=(?:and|then|while|but|so|after|before|"
    r"whereas|although)\b)", re.I)

UNIT_RE = re.compile(
    r"^\s*(%|percent\b|°?[CF]\b|[A-Za-zΩ°$€£/]+(?:/[A-Za-z]+)?)")
WORDNUM_RE = re.compile(
    r"\b((?:zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    r"eighty|ninety|hundred|thousand|million|half|third|quarter)"
    r"(?:[\s-](?:zero|one|two|three|four|five|six|seven|eight|nine|"
    r"ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    r"eighty|ninety|hundred|thousand|million|point))*)\b", re.I)
UNIT_WORDS = {"kg", "kilogram", "kilograms", "kilos", "kilo", "g",
              "gram", "grams", "m", "metre", "metres", "meter",
              "meters", "km", "cm", "mm", "s", "sec", "second",
              "seconds", "min", "minute", "minutes", "hour", "hours",
              "h", "hr", "hrs", "l", "litre", "litres", "liter",
              "liters", "ml", "v", "volt", "volts", "a", "amp",
              "amps", "ampere", "amperes", "ohm", "ohms", "w", "watt",
              "watts", "kw", "j", "joule", "joules", "kj", "kwh",
              "dollar", "dollars", "$", "eur", "euro", "euros", "%",
              "percent", "mol", "moles", "unit", "units", "item",
              "items", "piece", "pieces", "n", "newton", "newtons",
              "pa", "kpa", "hz", "degrees", "degree"}


# ------------------------------------------------- unit -> kind index
def _build_unit_index():
    idx = {}
    for kind, spec in KINDS9.items():
        dim, cu, nouns, aliases = (spec + ([],))[:4] if len(spec) >= 4 \
            else (spec[0], spec[1], spec[2], [])
        for u in [cu] + list(aliases or []):
            if not u:
                continue
            idx.setdefault(str(u).strip().lower(), []).append(kind)
    extra = {
        "metres": "m", "meters": "m", "metre": "m", "meter": "m",
        "kilograms": "kg", "kilogram": "kg", "kilos": "kg", "kilo": "kg",
        "grams": "g", "gram": "g", "seconds": "s", "second": "s",
        "sec": "s", "minutes": "min", "minute": "min", "hours": "h",
        "hour": "h", "hr": "h", "hrs": "h", "litres": "l", "liters": "l",
        "litre": "l", "liter": "l", "volts": "v", "volt": "v",
        "amps": "a", "amp": "a", "amperes": "a", "ampere": "a",
        "ohms": "ohm", "watts": "w", "watt": "w", "joules": "j",
        "joule": "j", "dollars": "$", "dollar": "$", "euros": "$",
        "euro": "$", "percent": "%", "moles": "mol", "newtons": "n",
        "newton": "n", "units": "unit", "items": "unit",
        "pieces": "unit", "piece": "unit", "item": "unit",
        "degrees": "°c", "degree": "°c", "kg/m": "kg/m^3",
        "km/h": "m/s", "kph": "m/s", "km/hr": "m/s",
    }
    for a, b in extra.items():
        if b in idx:
            idx.setdefault(a, idx[b])
    if "batches_month" in KINDS9:
        idx["batches/month"] = ["batches_month"]
        idx["batches/mo"] = ["batches_month"]
    return {u: sorted(set(ks)) for u, ks in idx.items()}


_UNIT_IDX = _build_unit_index()

# unit-string -> (canonical-family unit, factor). Conversion applies
# only when the resolved kind's canonical unit matches the family
# base; otherwise the raw value is kept (documented in the matrix).
_CONV = {
    "min": ("s", 60.0), "minutes": ("s", 60.0), "minute": ("s", 60.0),
    "h": ("s", 3600.0), "hr": ("s", 3600.0), "hrs": ("s", 3600.0),
    "hour": ("s", 3600.0), "hours": ("s", 3600.0),
    "km": ("m", 1000.0), "cm": ("m", 0.01), "mm": ("m", 0.001),
    "ml": ("l", 0.001), "kw": ("w", 1000.0), "kj": ("j", 1000.0),
    "kwh": ("j", 3.6e6),
}


def convert_to_canonical(value, unit, kind):
    """30 'minutes' for a seconds-canonical kind -> 1800. Returns
    (value, converted?)."""
    u = (unit or "").strip().lower().rstrip(".,;:!?")
    if u in _CONV and kind in KINDS9:
        base, f = _CONV[u]
        canon = str(KINDS9[kind][1] or "").strip().lower()
        if canon == base:
            return value * f, True
    return value, False


# dimension adjectives -> kind (the LLM knew these implicitly; the
# deterministic worker needs them spelled out)
_ADJ = {"long": "length", "wide": "width", "thick": "height",
        "across": "width", "tall": "height", "high": "height",
        "deep": "height",
        "moving": "speed", "travelling": "speed", "traveling": "speed",
        "cruises": "speed", "rolls": "speed"}


def _kind_noun_score(kind, window_tokens):
    nouns = [n.lower() for n in (KINDS9[kind][2] or [])] + \
        [kind.replace("_", " ")] + \
        [a for a, k in _ADJ.items() if k == kind]
    score = 0
    wt = set(window_tokens)
    joined = " ".join(window_tokens)
    for n in nouns:
        if " " in n:
            if n in joined:
                score += 3
        elif n in wt:
            score += 2
        else:
            stem = n.rstrip("s")
            if stem and any(t.startswith(stem) for t in wt):
                score += 1
    return score


_MOD_TOKS = {"sum", "total", "mean", "average", "squared",
             "deviations"}
_STOPS = {"of", "the", "a", "an", "per", "number"}


def phrase_name(clause, rel, known, unit=""):
    """Position-aware naming inside the mention's clause.
    1. exact kind noun-phrase present -> longest, then nearest;
    2. cardinal-count rule: unitless numeral + adjacent plural head
       noun -> the count-style kind (phrase without sum/total/mean
       modifiers, e.g. 'number of readings');
    3. distance-gated token vote (unique winner).
    Returns (kind_or_UNKNOWN, candidates)."""
    cl = clause.lower()
    words = re.findall(r"[a-z0-9.]+", cl)
    off, widx = 0, len(words) - 1
    for i, w in enumerate(words):
        j = cl.find(w, off)
        if j <= rel < j + len(w) or j > rel:
            widx = i
            break
        off = j + len(w)
    nxt = words[widx + 1:widx + 3]
    prv = words[max(0, widx - 3):widx]
    u = (unit or "").strip().lower()
    money_u = u.startswith("$") or u in ("dollars", "dollar")
    # pattern rules consult the FULL kind space: their triggers are
    # specific enough to override an uninformative unit-candidate set.
    # Each is UNIT-GATED (a % can never be a price or a count).
    if money_u and "price_per_unit" in KINDS9:
        if (nxt and nxt[0] in ("each", "apiece")) or \
                any(w.startswith(("sell", "sold", "price", "charg",
                                  "fetch")) for w in prv + nxt):
            return "price_per_unit", ["price_per_unit"]
    if u == "":
        # production-count: yields/produces/makes NUMBER <plural>
        if "count" in KINDS9 and prv and \
                any(w.startswith(("yield", "produc", "make", "output",
                                  "manufactur")) for w in prv):
            return "count", ["count"]
        # aggregate-sum: 'sums/totals to NUMBER' (plain, not squared)
        if "data_sum" in KINDS9 and len(prv) >= 2 and \
                prv[-1] == "to" and prv[-2].startswith(
                    ("sum", "total")):
            return "data_sum", ["data_sum"]
        # single observation: 'reading/observation/value of NUMBER'
        if "obs_value" in KINDS9 and len(prv) >= 2 and \
                prv[-1] == "of" and prv[-2].startswith(
                    ("reading", "observ", "measurement", "value")):
            return "obs_value", ["obs_value"]
    # cardinal-count: numeral immediately followed by a plural
    # head noun is the strongest local evidence (beats any distant
    # phrase in the same clause). If SEVERAL count kinds share the
    # head, fall through to position-aware phrase resolution.
    count_matches = []
    for kind in sorted(known):
        dim = KINDS9[kind][0]
        pure_count = (dim[5] == 1 and
                      sum(abs(d) for d in dim) == 1) or \
            all(d == 0 for d in dim)
        if not pure_count:
            continue        # a cardinal count can only BE a count
        for noun in (KINDS9[kind][2] or []):
            toks = [x for x in noun.lower().split()
                    if x not in _STOPS]
            if not toks or (set(toks) & _MOD_TOKS):
                continue
            head = toks[-1].rstrip("s")
            if head and any(w.startswith(head) for w in nxt):
                count_matches.append(kind)
                break
    if len(count_matches) == 1:
        return count_matches[0], count_matches
    hits = []
    for kind in known:
        for noun in list(KINDS9[kind][2] or []) + \
                [kind.replace("_", " ")]:
            n = noun.lower()
            j = cl.find(n)
            if j >= 0 and " " in n:
                hits.append((len(n.split()), -abs(j - rel), kind, n))
    if hits:
        hits.sort(reverse=True)
        top = hits[0]
        ties = {h[2] for h in hits
                if h[0] == top[0] and h[1] == top[1]}
        if len(ties) == 1:
            return top[2], [top[2]]
    # distance-gated token vote (±5 words)
    wset = set(words[max(0, widx - 5):widx + 6])
    votes = []
    for kind in sorted(known):
        sc = 0
        for noun in list(KINDS9[kind][2] or []) + \
                [kind.replace("_", " ")] + \
                [a for a, k2 in _ADJ.items() if k2 == kind]:
            for tk in noun.lower().split():
                if tk in _STOPS:
                    continue
                stem = tk.rstrip("s")
                if tk in wset or (stem and any(
                        w.startswith(stem) for w in wset)):
                    sc += 1
        if sc:
            votes.append((sc, kind))
    votes.sort(key=lambda x: (-x[0], x[1]))
    if votes and (len(votes) == 1 or votes[0][0] > votes[1][0]):
        return votes[0][1], [votes[0][1]]
    return "UNKNOWN", sorted({k for _, k in votes[:4]})


def _local_tokens(clause, rel, radius=3, forward_only=False):
    """Tokens within ±radius word-positions of the mention (or only
    the following `radius` tokens when forward_only)."""
    cl = clause.lower()
    words = re.findall(r"[a-z0-9.^/$%]+", cl)
    off, widx = 0, len(words) - 1
    for i, w in enumerate(words):
        j = cl.find(w, off)
        if j <= rel < j + len(w) or j > rel:
            widx = i
            break
        off = j + len(w)
    if forward_only:
        return words[widx + 1:widx + 1 + radius]
    return words[max(0, widx - radius):widx + radius + 1]


def name_concept(unit, tight_window, known, clause=None, rel=0):
    """Unit-dimension first, qualifier-noun tie-break, position-aware
    phrase fallback. Returns (kind_or_UNKNOWN, candidates, how)."""
    if clause is not None:
        toks = _local_tokens(clause, rel)
    else:
        toks = re.sub(r"[^a-z0-9\s/]", " ",
                      tight_window.lower()).split()
    u = (unit or "").strip().lower().rstrip(".,;:!?")
    lookup = u
    if u and u not in _UNIT_IDX and u in _CONV:
        lookup = _CONV[u][0]
    cands = [k for k in _UNIT_IDX.get(lookup, []) if k in known] \
        if u else []
    if len(cands) == 1:
        return cands[0], cands, "unit_unique"
    if len(cands) > 1:
        # forward micro-window first: 'NUMBER unit ADJECTIVE' is the
        # canonical dimension pattern (2 m long / 1 m wide)
        if clause is not None:
            fw = _local_tokens(clause, rel, radius=2,
                               forward_only=True)
            f_sc = sorted(((_kind_noun_score(k, fw), k)
                           for k in cands), reverse=True)
            if f_sc[0][0] > 0 and (len(f_sc) == 1 or
                                   f_sc[0][0] > f_sc[1][0]):
                return f_sc[0][1], cands, "unit+fwd"
        scored = sorted(((_kind_noun_score(k, toks), k)
                         for k in cands), reverse=True)
        if scored[0][0] > 0 and (len(scored) == 1 or
                                 scored[0][0] > scored[1][0]):
            return scored[0][1], cands, "unit+noun"
        if clause is not None:
            k2, _c2 = phrase_name(clause, rel, set(cands), unit=u)
            if k2 != "UNKNOWN":
                return k2, cands, "unit+position"
        return "UNKNOWN", cands, "unit_ambiguous"
    # no informative unit: position-aware clause naming
    if clause is not None:
        k2, c2 = phrase_name(clause, rel, known, unit=u)
        if k2 != "UNKNOWN":
            return k2, c2, "phrase_pos"
        if c2:
            return "UNKNOWN", c2, "phrase_ambiguous"
    k = normalize_concept(None, tight_window, unit or None, known,
                          expand=False)
    if k != "UNKNOWN":
        return k, [k], "phrase"
    return "UNKNOWN", [], "none"


def segment_clauses(text):
    """-> list of (clause_text, char_start)."""
    out, pos = [], 0
    for part in SPLIT_RE.split(text):
        if part is None or not part.strip():
            continue
        start = text.find(part, pos)
        if start < 0:
            start = pos
        out.append((part.strip(), start))
        pos = start + len(part)
    return out or [(text, 0)]


def _clause_of(pos, clauses):
    ci = 0
    for i, (_, start) in enumerate(clauses):
        if pos >= start:
            ci = i
    return ci


def _unit_after(text, end):
    m = UNIT_RE.match(text[end:end + 24])
    if not m:
        return ""
    u = m.group(1).strip()
    # compound rate units: "dollars per kg" -> "$/kg"
    tail = text[end + m.end():end + m.end() + 14]
    pm = re.match(r"\s+per\s+([A-Za-z]+)", tail)
    if pm:
        base = {"dollars": "$", "dollar": "$", "euros": "$",
                "euro": "$"}.get(u.lower(), u)
        return f"{base}/{pm.group(1).lower().rstrip('.,;:!?')}"
    lw = u.lower().rstrip(".,;:!?")
    if lw in UNIT_WORDS or "/" in u or u in ("%", "$", "€", "£") or \
            lw.startswith(("kg", "kwh", "mol", "ohm", "volt", "amp",
                           "watt", "joule", "newton")) or \
            re.fullmatch(r"°?[CF]", u):
        return u.rstrip(".,;:!?")
    return ""


def _money_before(text, start):
    return text[max(0, start - 1):start] in ("$", "€", "£")


def _per_unit_after(text, end):
    """'$1.5 per kg' -> '/kg' suffix for a money-prefixed number."""
    pm = re.match(r"\s+per\s+([A-Za-z]+)", text[end:end + 14])
    if pm:
        return "/" + pm.group(1).lower().rstrip(".,;:!?")
    return ""


def extract_mentions(text):
    """All numeric mentions with verbatim spans, values, units,
    positions, clause ids. Digits first; word-numbers where they do
    not overlap a digit mention."""
    clauses = segment_clauses(text)
    mentions, taken = [], []
    for m in _NUM_RE.finditer(text):
        try:
            v = float(m.group(0).replace(",", ""))
        except ValueError:
            continue
        s, e = m.span()
        if s > 0 and text[s - 1] in "^_":       # exponent (kg/m^3)
            continue
        unit = _unit_after(text, e)
        if _money_before(text, s):
            unit = "$" + _per_unit_after(text, e)
            s -= 1
        ci = _clause_of(s, clauses)
        cs = clauses[ci][1]
        ce = clauses[ci + 1][1] if ci + 1 < len(clauses) else len(text)
        ws = max(cs, s - 34)
        span = text[ws:min(ce, e + 34)].rstrip()
        mentions.append({"value": v, "unit": unit, "start": s,
                         "end": e, "span": span, "clause": ci,
                         "span_off": ws})
        taken.append((s, e))
    for m in WORDNUM_RE.finditer(text):
        s, e = m.span()
        if any(ts < e and te > s for ts, te in taken):
            continue
        w = words_to_number(m.group(1).lower().replace("-", " "))
        if w is None:
            continue
        # skip bare "one" (article-like) unless a unit word follows
        unit = _unit_after(text, e)
        if abs(w - 1.0) < 1e-9 and not unit:
            continue
        ci = _clause_of(s, clauses)
        cs = clauses[ci][1]
        ce = clauses[ci + 1][1] if ci + 1 < len(clauses) else len(text)
        ws = max(cs, s - 34)
        span = text[ws:min(ce, e + 34)].rstrip()
        mentions.append({"value": float(w), "unit": unit, "start": s,
                         "end": e, "span": span, "clause": ci,
                         "span_off": ws})
    mentions.sort(key=lambda d: d["start"])
    return mentions, clauses


def role_of(clause_text, window, center=None):
    """Role + polarity + time context. NEAREST cue to the mention
    wins (V0.9 lesson: first-match let a distant 'was' hijack a
    current-price mention). `center` = mention offset inside window."""
    if len(QUOTE_RE.findall(window)) >= 2:
        return "example", "asserted", "quoted"
    if center is None:
        center = len(window) // 2
    hits = []
    for role in ("example", "hypothetical", "negated",
                 "historical", "future", "spec_rating"):
        for m in CUE_RE[role].finditer(window):
            hits.append((abs((m.start() + m.end()) // 2 - center),
                         0, role))
    for m in CUR_RE.finditer(window):
        hits.append((abs((m.start() + m.end()) // 2 - center),
                     1, "current"))
    if not hits:
        return "input", "asserted", "none"
    hits.sort()
    _, _, role = hits[0]
    if role == "current":
        return "input", "asserted", "present"
    pol = "negated" if role == "negated" else "asserted"
    tc = {"historical": "past", "future": "future"}.get(role, "none")
    r = {"negated": "negated", "future": "historical",
         "example": "example", "hypothetical": "hypothetical",
         "historical": "historical",
         "spec_rating": "distractor"}[role]
    return r, pol, tc


def _entity_of(clause_text):
    """Clause-subject heuristic: first noun-ish word group before the
    first verb/number."""
    words = re.sub(r"[^A-Za-z\s]", " ", clause_text).split()
    stop = {"a", "an", "the", "of", "on", "in", "at", "is", "are",
            "was", "were", "it", "its", "this", "that", "and", "then",
            "with", "for", "to", "by", "runs", "has", "have", "had",
            "will", "sits", "if", "what", "how", "much", "many"}
    picked = [w for w in words[:6] if w.lower() not in stop][:2]
    return " ".join(picked) if picked else "item"


def parse(query, query_id=None, known=None):
    """Main entry: query -> extended SQR matrix + budget accounting.
    Returns (matrix, info)."""
    t0 = time.perf_counter()
    known = known or set(KINDS9)
    mentions, clauses = extract_mentions(query)
    ents, qs = {}, []
    for i, m in enumerate(mentions):
        ct = clauses[m["clause"]][0]
        ent = _entity_of(ct)
        eid = None
        for k, v in ents.items():
            if v == ent:
                eid = k
        if eid is None:
            eid = f"E{len(ents)+1}"
            ents[eid] = ent
        role, pol, tc = role_of(ct, ct,
                                center=m["start"]
                                - clauses[m["clause"]][1])
        concept, cands, how = name_concept(
            m["unit"], m["span"], known, clause=ct,
            rel=m["start"] - clauses[m["clause"]][1])
        value = m["value"]     # verbatim; compile_state owns conversion
        converted = False
        # historical/current contrast pairs for same-unit prices etc.
        status = ("ok" if concept != "UNKNOWN" else
                  "ambiguous_concept" if cands else "unknown_concept")
        qs.append({"qid": f"Q{i+1}", "entity": eid, "concept": concept,
                   "value": value, "unit": m["unit"],
                   "unit_converted": converted,
                   "role": role, "depends_on": [],
                   "source_span": m["span"], "provenance": "USER_TEXT",
                   "ambiguous": status != "ok", "clause": m["clause"],
                   "polarity": pol, "time_context": tc,
                   "candidates": cands, "named_by": how,
                   "confidence": ("high" if status == "ok" and
                                  how.startswith("unit") else
                                  "med" if status == "ok" else "low"),
                   "status": status})
    # target from the ask clause: question focus = the LONGEST kind
    # noun-phrase, ties broken toward the LATEST position ("after-tax
    # profit per unit sold" -> ppu, not net_profit)
    segs = [s for s in re.split(r"[.?!]", query) if s.strip()]
    ask = segs[-1].strip() if segs else query
    askl = ask.lower()
    tc_hits = []
    for kind in known:
        for noun in list(KINDS9[kind][2] or []) + \
                [kind.replace("_", " ")]:
            n = noun.lower()
            j = askl.rfind(n)
            if j >= 0 and " " in n:
                tc_hits.append((len(n.split()), j, kind))
    if tc_hits:
        tc_hits.sort(reverse=True)
        tconcept = tc_hits[0][2]
    else:
        tconcept = normalize_concept(None, ask, None, known,
                                     expand=False)
    if tconcept == "UNKNOWN":
        # unit-word in the ask names the target dimension ("in
        # joules", "in mol/L"): unique kind of that unit wins
        for w in re.findall(r"[a-z/$%^.\w]+", askl):
            ks = _UNIT_IDX.get(w.rstrip("?,."), [])
            ks = [k for k in ks if k in known]
            if len(ks) == 1:
                tconcept = ks[0]
                break
    matrix = {
        "query_id": query_id, "schema": "v10-matrix/1",
        "entities": [{"entity_id": k, "name": v, "span": v}
                     for k, v in ents.items()],
        "quantities": qs,
        "assumptions": [],
        "target": {"concept": tconcept, "entity": None, "span": ask,
                   "unit": None},
        "ambiguity_flags": [q["qid"] for q in qs if q["ambiguous"]],
    }
    info = {
        "n_mentions": len(mentions), "n_clauses": len(clauses),
        "unknown_concepts": sum(1 for q in qs
                                if q["status"] != "ok"),
        "target_known": tconcept != "UNKNOWN",
        "wall_ms": (time.perf_counter() - t0) * 1e3,
    }
    return matrix, info
