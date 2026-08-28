"""V0.5 engine: V0.4 machinery + Section-20 integrity gate + Section-19
dependency-aware handoff + Section-26 conventional cache control.

Systems (Section 4 / 29):
  llm_only        A: the optimized LLM answers every query directly.
  frozen_reflex   B: V0.4 partial engine (expression handoff), registry
                  frozen at v0. No breeder.
  reflex_breeder  C/D: same engine but the registry grows via breeder
                  generations (the lifetime driver swaps registries in).
  cache_llm       I: optimized LLM + conventional normalized-query cache.

V5Engine flags:
  integrity=True   run check_state between parser and planner; HARD flag
                   -> never trust reflex state; escalate whole query.
  depaware=True    gap detection via v5.depplan (contracts in prompt);
                   False -> V0.4 forward-only find_gap (ablation H).
"""
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401,E402
from src.llm import ollama_client as llm      # noqa: E402
from v4.engines_v4 import V4Engine, NoiseModel  # noqa: E402
from v4.qparse4 import parse_quantities, asked_kind  # noqa: E402
from v4 import partial_planner as PP          # noqa: E402
from v5.integrity import check_state          # noqa: E402
from v5 import depplan                        # noqa: E402
from v5.bridge5 import solve_gap_structured_v5  # noqa: E402


class V5Engine(V4Engine):
    def __init__(self, mode="partial", integrity=True, depaware=True,
                 **kw):
        super().__init__(mode=mode, **kw)
        self.integrity = integrity
        self.depaware = depaware
        self.name = f"v5_{mode}" + ("" if integrity else "_nointeg") + \
            ("" if depaware else "_nodep")
        if self.gap_solver is None and mode == "partial":
            self.gap_solver = solve_gap_structured_v5
        self._contracts = {}

    def process(self, query, mode_llm="hybrid", query_id=None, log=True):
        # corruption ground-truth label (for the Section-20 noise study):
        # replay the noise the engine WILL apply and compare to the clean
        # parse — recorded regardless of whether the gate is enabled
        corrupted = None
        if self.noise.parser_p > 0:
            st = self.noise.rng.getstate()
            qs_c, _ = parse_quantities(query)
            qs_n = self.noise.corrupt_quantities(list(qs_c))
            self.noise.rng.setstate(st)
            corrupted = ([(q.kind, q.value) for q in qs_c]
                         != [(q.kind, q.value) for q in qs_n])
        # Integrity gate runs FIRST on the (possibly noise-corrupted)
        # parse; a HARD flag disqualifies reflex computation entirely.
        if self.integrity:
            # snapshot the noise RNG so the corruption the gate inspects is
            # EXACTLY the corruption the engine will apply when it re-parses
            noise_state = self.noise.rng.getstate()
            qs, _ = parse_quantities(query)
            qs = self.noise.corrupt_quantities(qs)
            self.noise.rng.setstate(noise_state)
            ak = asked_kind(query)
            ig = check_state(query, qs, ak, registry=self.registry)
            if ig["hard"]:
                t0 = time.perf_counter()
                rec = {"query_id": query_id, "engine": self.name,
                       "mode": self.mode, "status": None, "answer": None,
                       "numeric_value": None, "reflex_ops": 0, "llm_ops": 0,
                       "llm_calls": 0, "llm_tokens": 0, "llm_flops": 0.0,
                       "reflex_flops": 0.0, "handoffs": [], "path": [],
                       "escalated": False, "integrity": ig,
                       "abstain_reason": "integrity:"
                       + ";".join(f["check"] for f in ig["flags"]
                                  if f["hard"]),
                       "registry_version": "v0"}
                if mode_llm == "hybrid":
                    rec["escalated"] = True
                    self._full_llm(rec, query)
                else:
                    rec["status"] = "ABSTAIN"
                if corrupted is not None:
                    rec["parse_corrupted"] = corrupted
                rec["total_ms"] = (time.perf_counter() - t0) * 1000
                return rec
        else:
            ig = None
        if self.depaware:
            # route the v4 engine's find_gap calls through depplan and
            # remember contracts so the solver wrapper can attach them
            self._contracts = {}
            orig_find = sys.modules["v4.engines_v4"].find_gap
            contracts = self._contracts

            def dep_find(qs2, ak2, priors=None, max_depth=6, registry=None,
                         suspect_mode=False):
                cands = depplan.find_gap_dep(
                    qs2, ak2, priors=priors, max_depth=max_depth,
                    registry=registry, suspect_mode=suspect_mode)
                for c in cands:
                    contracts[c["kind"]] = c.get("contract")
                return cands
            base_solver = solve_gap_structured_v5

            def solver_with_contract(q2, state2, kind2, existing2):
                return base_solver(q2, state2, kind2, existing2,
                                   contract=contracts.get(kind2))
            old_solver = self.gap_solver
            self.gap_solver = solver_with_contract
            sys.modules["v4.engines_v4"].find_gap = dep_find
            try:
                rec = super().process(query, mode_llm=mode_llm,
                                      query_id=query_id, log=log)
            finally:
                sys.modules["v4.engines_v4"].find_gap = orig_find
                self.gap_solver = old_solver
        else:
            rec = super().process(query, mode_llm=mode_llm,
                                  query_id=query_id, log=log)
        if ig is not None:
            rec["integrity"] = {"flags": ig["flags"], "hard": ig["hard"]}
        if corrupted is not None:
            rec["parse_corrupted"] = corrupted
        return rec


class LLMOnly:
    """System A: the optimized LLM answers everything directly."""
    name = "llm_only"

    def process(self, query, mode_llm="hybrid", query_id=None, log=True):
        t0 = time.perf_counter()
        out = llm.generate(query)
        return {"query_id": query_id, "engine": self.name, "mode": "llm",
                "status": "llm_answer", "answer": out["text"],
                "numeric_value": None, "reflex_ops": 0, "llm_ops": 1,
                "llm_calls": 1,
                "llm_tokens": out["prompt_tokens"] + out["gen_tokens"],
                "llm_flops": out["flops_est"], "reflex_flops": 0.0,
                "handoffs": [], "path": [], "escalated": True,
                "abstain_reason": None,
                "total_ms": (time.perf_counter() - t0) * 1000}


_WS = re.compile(r"\s+")
_NUM = re.compile(r"\d+(?:\.\d+)?")


class CachedLLM:
    """System I (Section 26): optimized LLM + conventional response cache.

    Two standard cache keys are measured:
      exact      the normalized query string (whitespace/case-folded) —
                 what a production response cache does.
    A structural cache that ignores the numbers is deliberately NOT a
    conventional cache (it would return wrong numbers for new values), so
    exact matching is the honest conventional control.
    """
    name = "cache_llm"

    def __init__(self):
        self.cache = {}
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key(query):
        return _WS.sub(" ", query.strip().lower())

    def process(self, query, mode_llm="hybrid", query_id=None, log=True):
        t0 = time.perf_counter()
        k = self.key(query)
        if k in self.cache:
            self.hits += 1
            ans = self.cache[k]
            return {"query_id": query_id, "engine": self.name,
                    "mode": "cache_hit", "status": "llm_answer",
                    "answer": ans, "numeric_value": None, "reflex_ops": 0,
                    "llm_ops": 0, "llm_calls": 0, "llm_tokens": 0,
                    "llm_flops": 0.0, "reflex_flops": 0.0, "handoffs": [],
                    "path": ["cache"], "escalated": False,
                    "cache_hit": True, "abstain_reason": None,
                    "total_ms": (time.perf_counter() - t0) * 1000}
        self.misses += 1
        out = llm.generate(query)
        self.cache[k] = out["text"]
        return {"query_id": query_id, "engine": self.name, "mode": "llm",
                "status": "llm_answer", "answer": out["text"],
                "numeric_value": None, "reflex_ops": 0, "llm_ops": 1,
                "llm_calls": 1,
                "llm_tokens": out["prompt_tokens"] + out["gen_tokens"],
                "llm_flops": out["flops_est"], "reflex_flops": 0.0,
                "handoffs": [], "path": [], "escalated": True,
                "cache_hit": False, "abstain_reason": None,
                "total_ms": (time.perf_counter() - t0) * 1000}
