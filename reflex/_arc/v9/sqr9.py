# -*- coding: utf-8 -*-
"""V0.9 Structured Query Representation (spec Sections 3-5, 36).

SQR schema (frozen before sealed evaluation; hash in provenance
manifest):

{
 "query_id": str,
 "entities": [{"entity_id": "E1", "name": str, "span": str}],
 "quantities": [{
   "qid": "Q1",
   "entity": "E1" | null,
   "concept": "<kind name>" | "UNKNOWN",
   "value": number | null,
   "unit": str | null,              # surface unit as written
   "role": "input" | "distractor" | "hypothetical" | "negated" |
           "historical" | "example" | "target",
   "relation": str | null,          # free-text relation tag
   "depends_on": ["Q#", ...],       # for DERIVED only
   "source_span": str,              # verbatim substring of the query
   "provenance": "USER_TEXT" | "DERIVED" | "ASSUMPTION" | "UNKNOWN",
   "ambiguous": bool
 }],
 "assumptions": [str],
 "target": {"concept": str | "UNKNOWN", "entity": str | null,
            "unit": str | null, "span": str},
 "ambiguity_flags": [str]
}

Leakage rule (Section 36): the SQR may never contain the final answer,
derived numeric values computed by the LLM, or a solution path. The
validator REJECTS any DERIVED quantity carrying a value (derivation is
the executor's job) and audits for answer leakage.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v9.universe9 import KINDS9                     # noqa: E402

ROLES = {"input", "distractor", "hypothetical", "negated", "historical",
         "example", "target"}
PROV = {"USER_TEXT", "DERIVED", "ASSUMPTION", "UNKNOWN"}

# ------------------------------------------------- number-word parsing
_ONES = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen"
    .split())}
_TENS = {w: 10 * i for i, w in enumerate(
    "zero ten twenty thirty forty fifty sixty seventy eighty ninety"
    .split())}
_SCALE = {"hundred": 100, "thousand": 1000, "million": 1e6,
          "billion": 1e9}
_FRAC = {"half": 0.5, "third": 1 / 3, "quarter": 0.25, "fourth": 0.25,
         "fifth": 0.2, "tenth": 0.1}


def words_to_number(text):
    """Parse a written number ('two', 'three and a half', 'twenty-five',
    'one hundred and four'). Returns float or None."""
    t = text.lower().replace("-", " ").strip()
    t = re.sub(r"\band\b", " ", t)
    toks = [w for w in t.split() if w and w != "a"]
    if not toks:
        return None
    total, cur, frac = 0.0, 0.0, 0.0
    seen = False
    for w in toks:
        if w in _ONES:
            cur += _ONES[w]; seen = True
        elif w in _TENS:
            cur += _TENS[w]; seen = True
        elif w in _SCALE:
            cur = (cur or 1) * _SCALE[w]; seen = True
        elif w in _FRAC:
            frac += _FRAC[w]; seen = True
        elif w in ("point",):
            continue
        else:
            return None
    if not seen:
        return None
    return total + cur + frac


_NUM_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?(?:[eE]-?\d+)?")


def span_values(span):
    """All numeric readings extractable from a source span: digits,
    scientific notation, simple fractions, percentages, written words.
    Returns a set of floats (raw and %-scaled where applicable)."""
    out = set()
    s = span.strip()
    for m in _NUM_RE.finditer(s):
        try:
            v = float(m.group(0).replace(",", ""))
        except ValueError:
            continue
        out.add(v)
        if "%" in s or "percent" in s.lower():
            out.add(v / 100.0)
    m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", s)
    if m and float(m.group(2)) != 0:
        out.add(float(m.group(1)) / float(m.group(2)))
    wtoks = re.sub(r"[^a-zA-Z\s-]", " ", s).split()
    for end in range(len(wtoks), 0, -1):
        w = words_to_number(" ".join(wtoks[:end]))
        if w is not None:
            out.add(w)
            if "percent" in s.lower():
                out.add(w / 100.0)
            break
    # common unit-conversion factors between span-literal and canonical
    base = set(out)
    for v in base:
        for f in (1e-3, 1e3, 60.0, 3600.0, 1 / 3.6, 3.6e6, 0.01, 100.0,
                  1e-2, 1e-6, 1e6, 0.25, 1 / 60, 1 / 3600):
            out.add(v * f)
    return out


# ------------------------------------------------------------ prompt
def kind_glossary(kinds=None, include_units=True):
    ks = kinds if kinds is not None else sorted(KINDS9)
    lines = []
    for k in ks:
        d, unit, nouns, _us = KINDS9[k]
        u = f" [{unit}]" if unit and include_units else ""
        lines.append(f"  {k}{u}: {nouns[0]}")
    return "\n".join(lines)


_EXAMPLE = """FORMAT: one line per element, fields separated by " | ".
  E <id> | <entity name> | <span>
  Q <id> | <entity id or -> | <concept> | <value> | <unit or -> | <role> | <source span copied verbatim>
  A | <assumption text>
  T | <target concept> | <entity id or -> | <target span>
  F | <ambiguity flag>
  END

EXAMPLE.
Query: "The lorry, not 9 kg but 1200 kg after weighing, rolls at
5 m/s past bay 7. What is its kinetic energy?"
Output:
E E1 | lorry | The lorry
Q Q1 | E1 | mass | 9 | kg | negated | not 9 kg
Q Q2 | E1 | mass | 1200 | kg | input | 1200 kg
Q Q3 | E1 | speed | 5 | m/s | input | 5 m/s
Q Q4 | - | UNKNOWN | 7 | - | distractor | bay 7
T | energy | E1 | kinetic energy
END
"""


def parse_compact(text):
    """Compact transport -> canonical SQR dict. Returns None if no Q/T
    structure found."""
    ents, qs, assum, flags = [], [], [], []
    tgt = None
    for raw in text.splitlines():
        line = raw.strip().strip("`")
        if not line or line == "END":
            continue
        parts = [p.strip() for p in line.split("|")]
        head = parts[0].split()
        tag = head[0].upper() if head else ""
        if tag == "E" and len(parts) >= 3:
            ents.append({"entity_id": head[1] if len(head) > 1 else
                         f"E{len(ents)+1}", "name": parts[1],
                         "span": parts[2]})
        elif tag == "Q" and len(parts) >= 6:
            # tolerant field alignment: value = first numeric field
            # after the concept (models occasionally insert extras)
            vi = None
            val = None
            for j in range(3, min(len(parts), 6)):
                try:
                    val = float(parts[j].replace(",", ""))
                    vi = j
                    break
                except ValueError:
                    continue
            if vi is None:
                vi = 3
            unit = parts[vi + 1] if len(parts) > vi + 1 else None
            role = parts[vi + 2].lower() if len(parts) > vi + 2 else \
                "input"
            span_f = parts[vi + 3] if len(parts) > vi + 3 else ""
            if role not in ROLES:
                role, span_f = "input", role + " " + span_f
            qs.append({"qid": head[1] if len(head) > 1 else
                       f"Q{len(qs)+1}",
                       "entity": None if parts[1] in ("-", "") else
                       parts[1],
                       "concept": " ".join(parts[2:vi]) or parts[2],
                       "value": val,
                       "unit": None if (unit or "") in ("-", "") else
                       unit,
                       "role": role, "source_span": span_f.strip(),
                       "provenance": "USER_TEXT", "ambiguous": False})
        elif tag == "A" and len(parts) >= 2:
            assum.append(parts[1])
        elif tag == "T" and len(parts) >= 2:
            tgt = {"concept": parts[1],
                   "entity": None if len(parts) < 3 or
                   parts[2] in ("-", "") else parts[2],
                   "unit": None,
                   "span": parts[3] if len(parts) > 3 else ""}
        elif tag == "F" and len(parts) >= 2:
            flags.append(parts[1])
    if not qs and tgt is None:
        return None
    return {"query_id": None, "entities": ents, "quantities": qs,
            "assumptions": assum, "target": tgt or {},
            "ambiguity_flags": flags}


def sqr_prompt(query, query_id, kinds=None):
    return (
        "You are a semantic parser. Convert the QUERY at the end into "
        "a Structured Query Representation (SQR). Do NOT solve the "
        "problem. Do NOT compute any value. Only represent what the "
        "text says.\n\n"
        "CONCEPT GLOSSARY (use exactly these concept names; "
        "\"UNKNOWN\" if none fits):\n" + kind_glossary(kinds) + "\n\n"
        "Rules:\n"
        "- EVERY number in the query text becomes one quantity entry, "
        "with source_span COPIED VERBATIM from the query.\n"
        "- provenance is \"USER_TEXT\" for anything read from the "
        "text. NEVER invent values, constants, units, or entities. "
        "Standard constants (g=9.8) are the executor's job.\n"
        "- role \"input\" only for numbers that describe the actual "
        "current problem. Negated numbers -> \"negated\"; if/would/"
        "imagine -> \"hypothetical\"; last year/used to/once -> "
        "\"historical\"; quoted or for-instance -> \"example\"; "
        "irrelevant -> \"distractor\".\n"
        "- Percentages: value as written (7 for 7%), unit \"%\".\n"
        "- Values exactly as written; written words become numbers "
        "('two kg' -> value 2, source_span 'two kg').\n"
        "- The target is what the question asks for; it has NO value.\n"
        "- Genuine ambiguity: ambiguous=true plus an ambiguity_flag. "
        "Never guess silently.\n\n"
        + _EXAMPLE + "\n"
        f"Now parse this QUERY (query_id \"{query_id}\"). Respond with "
        "ONLY the E/Q/A/T/F lines and END — no prose, no JSON.\n"
        f"QUERY: \"{query}\"")


# ---------------------------------------------------------- validator
def _norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


# ---------------------------------------------- concept normalization
# Deterministic alias layer (spec Section 15.7): reported concept
# strings and spans map onto glossary kinds. Curated core; the breeder
# may add learned aliases later. Built once from KINDS9 surfaces.
_STOP9 = set("the a an of per in to on for and or with each every"
             .split())


def _stem(t):
    for suf in ("ings", "ing", "ers", "er", "ed", "es", "s"):
        if t.endswith(suf) and len(t) - len(suf) >= 3:
            return t[: -len(suf)]
    return t


def _tokens(s):
    return [_stem(t) for t in re.findall(r"[a-z]+", (s or "").lower())
            if t not in _STOP9 and len(t) > 2]


def _build_alias_index():
    idx = {}
    for k, (d, unit, nouns, _u) in KINDS9.items():
        idx[k.lower()] = k
        idx[k.replace("_", " ").lower()] = k
        for n in nouns:
            idx[_norm(n)] = k
    return idx


_ALIAS = _build_alias_index()


def _noun_token_map():
    m = {}
    for k, (d, unit, nouns, _u) in KINDS9.items():
        for n in nouns:
            for t in _tokens(n):
                m.setdefault(t, set()).add(k)
    return m


_NOUN_TOK = _noun_token_map()


def _phrase_hits(text, known):
    """Longest noun-phrase exact matches in text (highest precedence)."""
    low = _norm(text)
    best = None
    for k, (d, unit, nouns, _u) in KINDS9.items():
        if k not in known:
            continue
        for n in nouns:
            nn = _norm(n)
            if nn and nn in low:
                if best is None or len(nn) > best[1]:
                    best = (k, len(nn))
    return best[0] if best else None


# unambiguous unit-surface -> kind (deterministic first-line alias)
_UNIT_ALIAS = {"$/kg": "price_per_kg", "$/kwh": "price_per_kwh",
               "$/unit": "price_per_unit", "$/item": "price_per_unit",
               "$/each": "price_per_unit", "$ each": "price_per_unit",
               "g/mol": "molar_mass", "kg/m^3": "density",
               "kg/m3": "density", "j/kg/k": "spec_heat",
               "m/s^2": "accel", "mol": "moles"}


def normalize_concept(concept, span=None, unit=None, known=None,
                      query=None, expand=True):
    """Reported concept string -> glossary kind, else 'UNKNOWN'.
    1. exact / snake-case / noun-phrase alias match;
    2. longest exact noun-phrase inside span (or its query window);
    3. token vote over noun phrases (unique winner only);
    4. unit-dimension inference (unique kind of that dimension).
    A bare-number span is expanded to a +-40-char window of the query."""
    known = known or set(KINDS9)
    c = _norm(concept)
    if c in ("", "unknown", "none", "null"):
        c = None
    if c:
        k = _ALIAS.get(c) or _ALIAS.get(c.replace("-", " "))
        if k in known:
            return k
        cs = c.replace(" ", "_")
        if cs in known:
            return cs
    ua = _UNIT_ALIAS.get(_norm(unit))
    if ua and ua in known:
        return ua
    ctx = span or ""
    if expand and query and span:
        i = _norm(query).find(_norm(span))
        if i >= 0:
            qn = _norm(query)
            ctx = qn[max(0, i - 60): i + len(_norm(span)) + 30]
    # longest exact phrase beats everything after direct alias — but
    # ONLY over the reported concept + literal span (the expanded
    # window may contain other sentences' phrases)
    ph = _phrase_hits((c or "") + " ; " + (span or ""), known)
    if ph:
        return ph
    # token vote
    votes = {}
    for src in (concept, ctx):
        for t in _tokens(src or ""):
            for k in _NOUN_TOK.get(t, ()):
                if k in known:
                    votes[k] = votes.get(k, 0) + 1
    if votes:
        top = sorted(votes.items(), key=lambda kv: -kv[1])
        if len(top) == 1 or top[0][1] > top[1][1]:
            return top[0][0]
    # unit-dimension inference
    if unit:
        from v9.universe9 import KINDS9 as K9
        u = _norm(unit)
        matches = {k for k, (d, cu, _n, us) in K9.items()
                   if k in known and
                   (u == _norm(cu) or u in {_norm(x) for x in us})}
        if len(matches) == 1:
            return next(iter(matches))
    return "UNKNOWN"


def validate_sqr(sqr, query, known_kinds=None):
    """Deterministic validation (Section 5). Returns (clean_sqr, report).
    Rejected quantities get status='rejected' + reasons; they are
    EXCLUDED from compilation but preserved in the report."""
    known = set(known_kinds if known_kinds is not None else KINDS9)
    rep = {"checks": [], "rejected": [], "flags": [], "leakage": []}
    qn = _norm(query)
    ents = {e.get("entity_id") for e in sqr.get("entities", [])
            if isinstance(e, dict)}
    qids = set()
    clean_q = []
    for q in sqr.get("quantities", []):
        if not isinstance(q, dict):
            continue
        reasons = []
        qid = q.get("qid") or f"Q{len(qids) + 1}"
        qids.add(qid)
        prov = q.get("provenance")
        role = q.get("role")
        span = q.get("source_span") or ""
        val = q.get("value")
        if prov not in PROV:
            reasons.append("provenance:invalid")
        if role not in ROLES:
            reasons.append("role:invalid")
        if q.get("entity") and q["entity"] not in ents:
            reasons.append("entity:unknown_ref")
        for d in q.get("depends_on") or []:
            if d not in qids:
                reasons.append("dependency:unknown_or_forward")
        c = q.get("concept")
        if c not in known:
            # alias normalization before any downgrade (Section 15.7)
            k2 = normalize_concept(c, q.get("source_span"),
                                   q.get("unit"), known, query=query)
            if k2 != "UNKNOWN":
                q = {**q, "concept": k2}
                rep["flags"].append(f"{qid}:concept_aliased:{c}->{k2}")
            elif c != "UNKNOWN":
                q = {**q, "concept": "UNKNOWN"}
                rep["flags"].append(f"{qid}:concept_downgraded:{c}")
        if prov == "USER_TEXT":
            if _norm(span) not in qn:
                reasons.append("span:not_in_text")
            elif val is not None:
                vals = span_values(span)
                if not any(abs(val - v) <= 1e-9 * max(1, abs(v))
                           for v in vals):
                    reasons.append("span:value_mismatch")
            if val is None and role == "input":
                reasons.append("value:missing_for_user_text_input")
        if prov == "DERIVED":
            # Section 36: the LLM must not pre-compute derived values
            if val is not None:
                reasons.append("leakage:derived_value_from_llm")
                rep["leakage"].append(qid)
            if not q.get("depends_on"):
                reasons.append("derived:no_dependencies")
        if prov == "ASSUMPTION" and val is not None and \
                _norm(span) not in qn:
            reasons.append("assumption:carries_invented_value")
        if reasons:
            rep["rejected"].append({"qid": qid, "reasons": reasons,
                                    "quantity": q})
        else:
            clean_q.append(q)
    tgt = sqr.get("target") or {}
    if not tgt or not tgt.get("concept") or \
            tgt.get("concept") == "UNKNOWN":
        # deterministic recovery from the question clause (substrate-
        # side, like V0.8's question focus): last query segment
        segs = [s for s in re.split(r"[.?!]", query) if s.strip()]
        ask = segs[-1] if segs else query
        k2 = normalize_concept(None, ask, tgt.get("unit"), known,
                               expand=False)
        if k2 != "UNKNOWN":
            rep["flags"].append(f"target:recovered_from_ask:{k2}")
            tgt = {**tgt, "concept": k2, "span": ask.strip()}
        else:
            rep["flags"].append("target:missing")
    if isinstance(tgt.get("concept"), str) and \
            tgt.get("concept") not in known:
        k2 = normalize_concept(tgt.get("concept"), tgt.get("span"),
                               tgt.get("unit"), known, query=query,
                               expand=False)
        if k2 != "UNKNOWN":
            rep["flags"].append(
                f"target:aliased:{tgt['concept']}->{k2}")
            tgt = {**tgt, "concept": k2}
        elif tgt.get("concept") != "UNKNOWN":
            rep["flags"].append(
                f"target:unknown_concept:{tgt['concept']}")
            tgt = {**tgt, "concept": "UNKNOWN"}
    if isinstance(tgt.get("concept"), str) and not tgt.get("span"):
        # empty target span: use the ask clause so phrase refinement
        # can see qualifiers ('final concentration', 'profit per unit')
        segs = [s for s in re.split(r"[.?!]", query) if s.strip()]
        if segs:
            tgt = {**tgt, "span": segs[-1].strip()}
    if isinstance(tgt.get("concept"), str) and tgt.get("span") and \
            tgt.get("concept") in known:
        # longest-phrase precedence: if the target SPAN contains a
        # LONGER noun phrase of a different kind that subsumes the
        # reported kind's phrase ('final concentration' over
        # 'concentration'), prefer the longer phrase's kind
        ph = _phrase_hits(tgt["span"], known)
        if ph and ph != tgt["concept"]:
            cur_nouns = [_norm(n) for n in KINDS9[tgt["concept"]][2]] \
                + [tgt["concept"].replace("_", " ")]
            ph_nouns = [_norm(n) for n in KINDS9[ph][2]]
            if any(cn in pn for cn in cur_nouns for pn in ph_nouns):
                rep["flags"].append(
                    f"target:phrase_refined:{tgt['concept']}->{ph}")
                tgt = {**tgt, "concept": ph}
    # leakage audit: any numeric in target?
    if isinstance(tgt.get("value", None), (int, float)):
        rep["leakage"].append("target_value")
        tgt = {k: v for k, v in tgt.items() if k != "value"}
    clean = {**sqr, "quantities": clean_q, "target": tgt}
    rep["n_in"] = len(sqr.get("quantities", []))
    rep["n_kept"] = len(clean_q)
    return clean, rep


# ---------------------------------------------------------- compiler
def compile_state(sqr, query):
    """Validated SQR -> typed quantities + target for the V0.8 Path
    Manager. Only role=input, provenance USER_TEXT/ASSUMPTION quantities
    become state. Percent-unit values are scaled to fractions for
    rate-dimension kinds (documented conversion)."""
    from v3.ir import Quantity
    from v9.universe9 import dim_of, D0
    qs, meta = [], []
    # context-sensitive alias: in a chemistry frame (molar_mass /
    # concentration present), a generic 'mass' in grams IS the solute
    # mass (deterministic, dimension-compatible re-kind)
    kinds_present = {q.get("concept") for q in sqr.get("quantities", [])}
    chem_frame = bool(kinds_present & {"molar_mass", "concentration",
                                       "moles", "dilution_factor"})
    for q in sqr.get("quantities", []):
        if chem_frame and q.get("concept") == "mass" and \
                "g" == (q.get("unit") or "").strip().lower()[:1] and \
                "kg" not in (q.get("unit") or "").lower():
            q = {**q, "concept": "solute_mass"}
        if chem_frame and q.get("concept") == "volume" and \
                (q.get("unit") or "").strip().lower() in (
                    "l", "litres", "liters", "ml"):
            q = {**q, "concept": "solution_volume"}
        if q.get("role") != "input" or q.get("value") is None:
            continue
        if q.get("provenance") not in ("USER_TEXT", "ASSUMPTION"):
            continue
        kind = q.get("concept")
        if kind in (None, "UNKNOWN"):
            continue
        val = float(q["value"])
        unit = (q.get("unit") or "").strip()
        if unit in ("%", "percent") or "percent" in unit.lower():
            # scale only when plainly written as a percentage (guard:
            # an already-fractional 0.06 tagged '%' must not rescale)
            if dim_of(kind) == D0 and abs(val) > 1.5:
                val = val / 100.0
        # unit normalization for common written variants
        u = unit.lower()
        if kind == "mass" and u in ("g", "grams", "gram"):
            val = val / 1000.0   # physics mass canonical kg
        if kind == "mass" and u in ("t", "tonnes", "tonne",
                                    "metric tons"):
            val = val * 1000.0
        if kind == "time" and u in ("min", "minute", "minutes"):
            val = val * 60.0
        if kind == "time" and u in ("h", "hr", "hrs", "hour", "hours"):
            val = val * 3600.0
        if kind == "speed" and u in ("km/h", "kph"):
            val = val / 3.6
        if kind == "energy" and u in ("kj",):
            val = val * 1e3
        if kind == "energy" and u in ("mj",):
            val = val * 1e6
        if kind == "energy" and u in ("kwh",):
            val = val * 3.6e6
        if kind == "power" and u in ("kw",):
            val = val * 1e3
        if kind == "price_per_kwh" and ("kwh" in u or u in ("$", "")):
            val = val / 3.6e6   # canonical $/J for the energy_cost cap
        if kind == "solution_volume" and u in ("ml", "millilitres",
                                               "milliliters"):
            val = val / 1000.0
        qs.append(Quantity(kind=kind, value=val))
        meta.append({"qid": q.get("qid"), "kind": kind,
                     "span": q.get("source_span")})
    tgt = (sqr.get("target") or {}).get("concept")
    if tgt == "UNKNOWN":
        tgt = None
    return qs, tgt, meta


# ------------------------------------------------------------ grading
def grade_sqr(sqr, truth):
    """Field-wise grading vs ground-truth SQR (Section 7 metrics).
    truth: {"quantities": [{concept,value,unit_ok?,role,entity_group}],
            "target": concept, "n_entities": int}
    Matching: greedy by (value); each truth quantity consumed once."""
    got = list(sqr.get("quantities", []))
    res = {"q_total": len(truth["quantities"]), "q_value": 0,
           "q_concept": 0, "q_role": 0, "q_unit": 0, "q_full": 0,
           "extra_inputs": 0, "target_ok": False,
           "unsupported_values": 0}
    used = set()
    for t in truth["quantities"]:
        best = None
        for i, g in enumerate(got):
            if i in used or g.get("value") is None:
                continue
            if abs(g["value"] - t["value"]) <= 1e-6 * max(1, abs(t["value"])):
                best = i
                break
        if best is None:
            continue
        used.add(best)
        g = got[best]
        res["q_value"] += 1
        c_ok = g.get("concept") == t["concept"]
        r_ok = g.get("role") == t["role"]
        u_ok = True if t.get("unit") is None else \
            _norm(g.get("unit")) == _norm(t["unit"])
        res["q_concept"] += c_ok
        res["q_role"] += r_ok
        res["q_unit"] += u_ok
        res["q_full"] += (c_ok and r_ok and u_ok)
    # extra role=input quantities not in truth inputs = wrong-field risk
    truth_input_vals = {round(t["value"], 9) for t in truth["quantities"]
                        if t["role"] == "input"}
    for i, g in enumerate(got):
        if g.get("role") == "input" and g.get("value") is not None and \
                round(g["value"], 9) not in truth_input_vals and \
                not any(abs(g["value"] - t["value"]) <= 1e-6 *
                        max(1, abs(t["value"]))
                        for t in truth["quantities"]):
            res["extra_inputs"] += 1
    res["target_ok"] = (sqr.get("target") or {}).get("concept") == \
        truth["target"]
    res["complete"] = (res["q_full"] == res["q_total"] and
                       res["target_ok"] and res["extra_inputs"] == 0)
    return res


def sqr_schema_hash():
    import hashlib
    doc = Path(__file__).read_text(encoding="utf-8")
    m = re.search(r'"""(.*?)"""', doc, re.S)
    return hashlib.sha256(m.group(1).encode()).hexdigest()[:16]
