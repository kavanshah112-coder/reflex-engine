# -*- coding: utf-8 -*-
# origin: new for V1.3 — W1 retrieval typing (V1_3_SPEC §4)
"""The FRAME: given a query, return the small slice of the domain a
parser should reason over — candidate kinds, capabilities, constants
and worked examples — or NO FRAME, which is an early abstention
signal rather than a failure.

Tier 1 is a hashed n-gram nearest-neighbour index (V0.2 lineage: OOD
AUROC 0.993 at ~1/200,000 the cost of embeddings). No training, no
model, no embedder — a bag of hashed character and token n-grams,
cosine similarity, top-k neighbours.

The index is LABELLED FOR FREE: every in-universe traffic item is run
through the engine once, and the kinds that appear in its certified
facts plus its target kind become that item's frame label. The engine
teaches the frame what its own vocabulary looks like in language.

Rule (V1_3_SPEC §4): the frame is EVIDENCE, NOT AUTHORITY. It narrows
the candidate space and nothing else — every downstream check still
runs on its own terms, and a frame that cannot type every quantity in
the text is a signal to widen or abstain, never to drop the leftovers.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

N_BUCKETS = 2 ** 15
TOK_RE = re.compile(r"[a-z0-9]+")


def features(text):
    """Hashed bag of token unigrams/bigrams + character 4-grams."""
    t = text.lower()
    toks = TOK_RE.findall(t)
    grams = list(toks)
    grams += [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
    squashed = re.sub(r"\s+", " ", t)
    grams += [squashed[i:i + 4] for i in range(0, len(squashed) - 3, 2)]
    v = Counter()
    for g in grams:
        v[hash(g) % N_BUCKETS] += 1
    norm = math.sqrt(sum(c * c for c in v.values())) or 1.0
    return {k: c / norm for k, c in v.items()}


def cosine(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(w * b.get(k, 0.0) for k, w in a.items())


class FrameIndex:
    def __init__(self):
        self.rows = []          # {vec, kinds, caps, q, target}
        self.no_frame_threshold = 0.0
        self.all_kinds = []

    # ---------------------------------------------------- build
    @staticmethod
    def label_item(engine, query, qid):
        """Run the engine once; harvest the kinds it actually used."""
        r = engine.run_query(query, qid)
        st, info = r.get("_state"), r.get("_info") or {}
        kinds = set()
        if st is not None:
            for f in st.facts:
                c = f.get("concept")
                if c and c != "UNKNOWN":
                    kinds.add(c)
        tgt = info.get("target_concept")
        if tgt and tgt != "UNKNOWN":
            kinds.add(tgt)
        return kinds, (r.get("numeric_value") is not None)

    def build(self, engine, items, limit=None, require_solved=True):
        n_lab = 0
        for it in (items[:limit] if limit else items):
            kinds, solved = self.label_item(engine, it["q"],
                                            f"fi_{it.get('id', n_lab)}")
            if require_solved and not solved:
                continue
            if not kinds:
                continue
            self.rows.append({"vec": features(it["q"]),
                              "kinds": sorted(kinds),
                              "q": it["q"][:120]})
            n_lab += 1
        import v10.universe10 as U10
        self.all_kinds = sorted(U10.KINDS10)
        return n_lab

    def calibrate(self, held_out, percentile=5):
        """No-frame threshold = the `percentile`-th percentile of
        best-match scores on held-out IN-UNIVERSE queries, so ~95% of
        genuinely in-domain traffic still receives a frame. A stated
        rule, not a tuned number."""
        scores = sorted(self.best_score(x["q"]) for x in held_out)
        if not scores:
            return 0.0
        idx = max(0, int(len(scores) * percentile / 100) - 1)
        self.no_frame_threshold = scores[idx]
        return self.no_frame_threshold

    # ---------------------------------------------------- query
    def _neighbours(self, text, k):
        v = features(text)
        scored = [(cosine(v, r["vec"]), r) for r in self.rows]
        scored.sort(key=lambda x: -x[0])
        return scored[:k]

    def best_score(self, text):
        nb = self._neighbours(text, 1)
        return nb[0][0] if nb else 0.0

    def frame(self, text, k=8, max_kinds=15):
        """-> dict or None (no frame = early abstention signal)."""
        nb = self._neighbours(text, k)
        if not nb or nb[0][0] < self.no_frame_threshold:
            return None
        votes = Counter()
        for score, row in nb:
            for kd in row["kinds"]:
                votes[kd] += score
        kinds = [k_ for k_, _ in votes.most_common(max_kinds)]
        return {"kinds": kinds,
                "examples": [{"q": r["q"], "kinds": r["kinds"]}
                             for _s, r in nb[:3]],
                "score": nb[0][0],
                "n_kinds": len(kinds),
                "n_kinds_full": len(self.all_kinds)}

    # ---------------------------------------------------- io
    def save(self, path):
        Path(path).write_text(json.dumps({
            "threshold": self.no_frame_threshold,
            "all_kinds": self.all_kinds,
            "rows": [{"q": r["q"], "kinds": r["kinds"],
                      "vec": {str(k): round(v, 6)
                              for k, v in r["vec"].items()}}
                     for r in self.rows]}), encoding="utf-8")

    @classmethod
    def load(cls, path):
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        fi = cls()
        fi.no_frame_threshold = d["threshold"]
        fi.all_kinds = d["all_kinds"]
        fi.rows = [{"q": r["q"], "kinds": r["kinds"],
                    "vec": {int(k): v for k, v in r["vec"].items()}}
                   for r in d["rows"]]
        return fi
