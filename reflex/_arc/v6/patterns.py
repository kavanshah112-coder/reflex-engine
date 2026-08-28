# -*- coding: utf-8 -*-
"""V0.6 pattern layer (spec Sections 5, 11-I, 11-K).

A PATTERN is a learned surface->semantic binding with typed wildcard
slots. Two families:

  QPAT  quantity-binding pattern: the abstracted token context around a
        number -> quantity kind.
        e.g.  ('<N>', '<NOUNS>', 'at', '$<N>')  @ target 0  -> count
              ('$<N>', 'a', '<NOUN>')           @ target 0  -> price_per_unit
  APAT  asked-intent pattern: the abstracted final-question tokens ->
        asked kind.
        e.g.  ('how', 'much', 'do', 'they', '<W>')          -> profit
              ('what', 'does', 'it', '<W>', 'at')           -> mass

Abstraction replaces: numbers -> <N> / $<N> / <N>%, tokens known to the
kind lexicon stay literal, unknown content words -> <NOUN>/<NOUNS>/<W>
wildcards. Each stored pattern carries EVIDENCE (distinct value tuples,
source ids, verification flags) and a STATUS (candidate/deployed/blocked).
Patterns are learned ONLY by the breeder's structural-alignment miner and
deployed ONLY through the staged gate (gates6). Anti-patterns BLOCK a
binding; they can never enable one.

Recognition contract (engine6): a deployed QPAT may bind a number the
base parser left unbound, or re-kind the GENERIC kinds ('money',
'distance'); it must never override a specific base-parser kind. A
deployed APAT may fill asked_kind only when the base parser returns None
or the most-generic 'money'. This guarantees no regression on in-vocab
queries by construction.
"""
import json
import re
from pathlib import Path

_TOK = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?|\d[\d,]*(?:\.\d+)?\s?%|"
                  r"\d[\d,]*(?:\.\d+)?|[a-zA-Z][a-zA-Z'-]*|[?.!,;]")
_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")

# function words stay literal in abstractions
_STOP = set("""a an the of at per each every for in on to from with and or
what how much many money does do did is are was it its they them their he
she we you that this those these after before over under about around
if when where which who whom whose why will would can could should must
by as into onto out up down off no not""".split())
# domain words that stay literal (they carry the signal the base parser
# already uses; keeping them literal makes learned patterns compose with
# known vocabulary instead of wildcarding everything)
_KEEP = set("""cost costs price prices revenue profit interest rate tax
discount fixed unit units total kg kilogram kilograms liter liters litre
litres kwh kilowatt watt watts volt volts amp amps ampere amperes second
seconds hour hours year years m meter meters metre metres square cubic
sell sells sold sale make makes made produce produced compound compounds
compounded annually yearly simple percent invest deposit grows worth
balance earn earned pays paid bring brings bill billed overhead
overheads month months week weeks day days""".split())


def tokenize(text):
    return _TOK.findall(text)


def _abstract_token(tok, lexicon=None):
    t = tok.lower()
    if tok.startswith("$"):
        return "$<N>"
    if t.endswith("%") or (t[:-1].strip().replace(",", "").replace(
            ".", "").isdigit() and t.endswith("%")):
        return "<N>%"
    if _NUM.fullmatch(t.replace(",", "")):
        return "<N>"
    if t in _STOP or t in _KEEP or t in ".?!,;":
        return t
    if lexicon and t in lexicon:
        return t                       # learned lexeme stays literal
    # unknown content word -> wildcard, plural-aware
    if t.endswith("s") and len(t) > 3:
        return "<NOUNS>"
    return "<W>"


def abstract(tokens, lexicon=None):
    return tuple(_abstract_token(t, lexicon) for t in tokens)


def number_contexts(text, l=3, r=3):
    """[(value, currency, percent, abstraction_windows)] for every number
    token. Windows are (left+target+right) abstractions at granularities
    (3,3), (2,2), (1,1) — the matcher prefers the longest deployed one."""
    toks = tokenize(text)
    out = []
    for i, tok in enumerate(toks):
        t = tok.lower().replace(",", "")
        cur = tok.startswith("$")
        pct = t.endswith("%")
        core = t.lstrip("$ ").rstrip("% ")
        if not _NUM.fullmatch(core):
            continue
        val = float(core)
        if pct:
            val /= 100.0
        wins = {}
        for g in (3, 2, 1):
            lo, hi = max(0, i - g), min(len(toks), i + g + 1)
            wins[g] = (abstract(tuple(toks[lo:i]) + ("§",)
                                + tuple(toks[i + 1:hi])), i - lo)
        out.append({"value": val, "currency": cur, "percent": pct,
                    "tok_index": i, "windows": wins,
                    "raw_context": " ".join(toks[max(0, i - 3):i + 4])})
    return out


def question_abstraction(text, lexicon=None, max_len=12):
    """Abstracted tokens of the final question sentence."""
    segs = [s for s in re.split(r"[.!]", text) if s.strip()]
    q = segs[-1] if segs else text
    toks = tokenize(q)[-max_len:]
    return abstract(toks, lexicon)


def _key(abstraction):
    return "␟".join(abstraction[0] if isinstance(abstraction, tuple)
                         and len(abstraction) == 2
                         and isinstance(abstraction[0], tuple)
                         else abstraction)


class PatternRegistry:
    """Learned patterns + lexicon + anti-patterns, versioned."""

    def __init__(self):
        self.qpats = {}    # key -> {kind, evidence:[...], status, gran}
        self.apats = {}    # key -> {kind, evidence:[...], status}
        self.lexicon = {}  # lexeme -> {concept, evidence:[...], status}
        self.blocked = set()   # anti-pattern keys ("Q:"+key / "A:"+key)
        self.generation = 0

    # ---------- evidence (breeder-only) ----------
    def add_qpat_evidence(self, window_abs, target_pos, kind, value_tuple,
                          source_id, verified):
        k = f"{_key(window_abs)}@{target_pos}"
        e = self.qpats.setdefault(k, {"kind": kind, "abstraction":
                                      list(window_abs),
                                      "target_pos": target_pos,
                                      "evidence": [], "status":
                                      "candidate", "conflicts": 0})
        if e["kind"] != kind:
            e["conflicts"] += 1
            return False
        if any(x["source"] == source_id for x in e["evidence"]):
            return True                 # generational re-mining dedupe
        e["evidence"].append({"values": list(value_tuple),
                              "source": source_id, "verified": verified})
        return True

    def add_apat_evidence(self, q_abs, kind, source_id, verified):
        k = _key(q_abs)
        e = self.apats.setdefault(k, {"kind": kind,
                                      "abstraction": list(q_abs),
                                      "evidence": [], "status":
                                      "candidate", "conflicts": 0})
        if e["kind"] != kind:
            e["conflicts"] += 1
            return False
        if any(x["source"] == source_id for x in e["evidence"]):
            return True
        e["evidence"].append({"source": source_id, "verified": verified})
        return True

    def add_lexeme_evidence(self, lexeme, concept, source_id, verified):
        e = self.lexicon.setdefault(lexeme.lower(), {
            "concept": concept, "evidence": [], "status": "candidate",
            "conflicts": 0})
        if e["concept"] != concept:
            e["conflicts"] += 1
            return False
        if any(x["source"] == source_id for x in e["evidence"]):
            return True
        e["evidence"].append({"source": source_id, "verified": verified})
        return True

    # ---------- recognition (deployed patterns only) ----------
    def match_number(self, nc):
        """nc from number_contexts. Longest deployed window wins."""
        for g in (3, 2, 1):
            win, pos = nc["windows"][g]
            k = f"{_key(win)}@{pos}"
            if f"Q:{k}" in self.blocked:
                continue
            e = self.qpats.get(k)
            if e and e["status"] == "deployed":
                return {"kind": e["kind"], "pattern": k, "gran": g,
                        "evidence_n": len(e["evidence"])}
        return None

    def match_ask(self, q_abs):
        k = _key(q_abs)
        if f"A:{k}" in self.blocked:
            return None
        e = self.apats.get(k)
        if e and e["status"] == "deployed":
            return {"kind": e["kind"], "pattern": k,
                    "evidence_n": len(e["evidence"])}
        return None

    def lookup_lexeme(self, tok):
        e = self.lexicon.get(tok.lower())
        if e and e["status"] == "deployed":
            return e["concept"]
        return None

    def deployed_lexemes(self):
        return {t for t, e in self.lexicon.items()
                if e["status"] == "deployed"}

    def block(self, family, key, reason):
        self.blocked.add(f"{family}:{key}")
        tgt = self.qpats if family == "Q" else self.apats
        if key in tgt:
            tgt[key]["status"] = "blocked"
            tgt[key]["block_reason"] = reason

    # ---------- persistence ----------
    def stats(self):
        def n(d, st):
            return sum(1 for e in d.values() if e["status"] == st)
        return {"qpats": {"total": len(self.qpats),
                          "deployed": n(self.qpats, "deployed"),
                          "candidate": n(self.qpats, "candidate"),
                          "blocked": n(self.qpats, "blocked")},
                "apats": {"total": len(self.apats),
                          "deployed": n(self.apats, "deployed")},
                "lexicon": {"total": len(self.lexicon),
                            "deployed": n(self.lexicon, "deployed")},
                "blocked": len(self.blocked),
                "generation": self.generation}

    def save(self, path):
        Path(path).write_text(json.dumps(
            {"qpats": self.qpats, "apats": self.apats,
             "lexicon": self.lexicon, "blocked": sorted(self.blocked),
             "generation": self.generation}, indent=1,
            ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path):
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        pr = cls()
        pr.qpats = d["qpats"]
        pr.apats = d["apats"]
        pr.lexicon = d["lexicon"]
        pr.blocked = set(d["blocked"])
        pr.generation = d.get("generation", 0)
        return pr
