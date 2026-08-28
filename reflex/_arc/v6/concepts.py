# -*- coding: utf-8 -*-
"""V0.6 concept layer (spec Sections 6, 7).

Distinct from pattern matching (surface) and capability execution
(computation): the concept layer holds

  CONCEPT NODES   quantity kinds (count, price_per_unit, profit, ...),
                  domains (finance, physics, engineering), and ROLE
                  concepts (count_noun, price_context, ask verbs).
  CONCEPT EDGES   kind -consumed_by-> capability, capability -produces->
                  kind (derived from the live registry), domain edges,
                  and LEARNED lexeme->concept edges (from the alignment
                  miner, deployed through the gate).

The concept RECOGNIZER returns candidates with scores + provenance +
semantic evidence counts — it never executes anything (spec 6: keep
recognition and execution separable and separately measurable).
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401,E402
from v4 import registry_v4 as R4  # noqa: E402
from v6.patterns import tokenize, _STOP, _KEEP  # noqa: E402


class ConceptGraph:
    def __init__(self, registry=None, pattern_registry=None):
        self.reg = registry if registry is not None else R4.REGISTRY
        self.pr = pattern_registry
        self._build()

    def _build(self):
        self.nodes = set()
        self.edges = []          # (src, relation, dst, provenance)
        for name, spec in self.reg.items():
            if spec.get("transfer"):
                continue
            dom = spec.get("domain", "unknown")
            self.nodes.add(("capability", name))
            self.nodes.add(("domain", dom))
            self.edges.append((("capability", name), "in_domain",
                               ("domain", dom), "registry"))
            for k in spec["inputs"]:
                self.nodes.add(("kind", k))
                self.edges.append((("kind", k), "consumed_by",
                                   ("capability", name), "registry"))
            self.nodes.add(("kind", spec["output"]))
            self.edges.append((("capability", name), "produces",
                               ("kind", spec["output"]), "registry"))
        if self.pr:
            for lex, e in self.pr.lexicon.items():
                if e["status"] == "deployed":
                    self.nodes.add(("lexeme", lex))
                    self.edges.append((("lexeme", lex), "evokes",
                                       ("kind", e["concept"]),
                                       f"learned(n={len(e['evidence'])})"))

    def recognize(self, text):
        """Concept candidates for a query: kinds evoked by learned
        lexemes + kinds evoked by literal kind-vocabulary, with scores
        (= evidence counts, capped) and provenance. Purely lexical —
        the pattern layer handles positional binding."""
        toks = [t.lower() for t in tokenize(text)]
        cands = defaultdict(lambda: {"score": 0.0, "provenance": []})
        for t in toks:
            if self.pr:
                e = self.pr.lexicon.get(t)
                if e and e["status"] == "deployed":
                    c = cands[e["concept"]]
                    c["score"] += min(5, len(e["evidence"]))
                    c["provenance"].append(f"lexeme:{t}")
        ranked = sorted(cands.items(), key=lambda kv: -kv[1]["score"])
        return [{"concept": k, **v} for k, v in ranked]

    def stats(self):
        by_rel = defaultdict(int)
        for _, rel, _, prov in self.edges:
            by_rel[rel if prov == "registry" else f"{rel}(learned)"] += 1
        return {"nodes": len(self.nodes), "edges": len(self.edges),
                "by_relation": dict(by_rel)}

    def save(self, path):
        Path(path).write_text(json.dumps(
            {"nodes": sorted(map(list, self.nodes)),
             "edges": [[list(a), r, list(b), p]
                       for a, r, b, p in self.edges],
             "stats": self.stats()}, indent=1), encoding="utf-8")
