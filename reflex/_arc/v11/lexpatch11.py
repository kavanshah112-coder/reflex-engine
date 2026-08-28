# -*- coding: utf-8 -*-
"""V0.11 lexicon additions, applied AT RUNTIME to the v10 worker's
tables so that Control C1 (V0.10 unchanged) can still run the pure
v10 code in its own process. apply() is idempotent."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_APPLIED = False


def apply():
    global _APPLIED
    if _APPLIED:
        return
    import v10.nlpw10 as W
    W._ADJ.update({
        "falling": "height", "falls": "height", "fell": "height",
        "drops": "height", "dropped": "height", "descends": "height",
        "plunges": "height", "climbs": "height", "lifted": "height",
        "raised": "height", "hoisted": "height", "lowered": "height",
    })
    W._EXTRA_NOUNS.setdefault("height", []).extend(
        ["falling", "fall", "drop", "descent"])
    W._EXTRA_NOUNS.setdefault("speed", []).extend(
        ["velocity", "pace", "clip"])
    W._EXTRA_NOUNS.setdefault("mass", []).extend(
        ["weighs", "weighing", "weight", "weigh"])
    # unit-index additions (count-noun units)
    for u in ("pieces", "piece", "items", "item", "widgets",
              "units", "unit"):
        W._UNIT_IDX.setdefault(u, ["count"])
    # patched phrase_name: punctuation-stripped pattern tokens +
    # 'go for' sale verb (v11-only; C1 keeps pure v10 behavior)
    _orig_pn = W.phrase_name

    def _pn11(clause, rel, known, unit=""):
        import re as _re
        cl = clause.lower()
        words = _re.findall(r"[a-z0-9.^/$%]+", cl)
        off, widx = 0, len(words) - 1
        for i, w in enumerate(words):
            j = cl.find(w, off)
            if j <= rel < j + len(w) or j > rel:
                widx = i
                break
            off = j + len(w)
        nxt = [w.rstrip(".,;:!?") for w in words[widx + 1:widx + 3]]
        prv = [w.rstrip(".,;:!?")
               for w in words[max(0, widx - 3):widx]]
        u = (unit or "").strip().lower()
        money_u = u.startswith("$") or u in ("dollars", "dollar")
        if money_u and "price_per_unit" in W.KINDS9:
            if (nxt and nxt[0] in ("each", "apiece")) or                     any(w.startswith(("sell", "sold", "price",
                                      "charg", "fetch", "go",
                                      "goes", "went"))
                        for w in prv + nxt):
                return "price_per_unit", ["price_per_unit"]
        return _orig_pn(clause, rel, known, unit=unit)

    W.phrase_name = _pn11
    _APPLIED = True
