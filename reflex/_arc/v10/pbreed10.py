# -*- coding: utf-8 -*-
"""V0.10 breeder (spec Sections 7/24/25): three target classes.

1. PARSER transformations — reuses the proven V0.9 machinery
   (ParserBreeder: ±3-token <NUM> windows, gates G1 support /
   G2 replay / G3 held-out, ask-patterns) fed with V0.10 experience
   records (validated matrix + completed path; self-supervised, no
   ground truth). The V0.10 twist: observations come from system-G
   traffic INCLUDING case-B/C escalations, so patterns can capture
   transformations the deterministic worker alone could not name —
   converting LLM-assisted parses into future deterministic ones.
2. CAPABILITY mining — V0.6's result, not re-run (registry given);
   recorded as inherited.
3. PATH structures — (sorted kind signature, target) -> plan cache;
   deployment = cache entries replayed structurally (Section 35's
   structural reuse), revalidated by verify_executable on hit.

Pollution testing reuses pollute_sqr modes + adds wrong-role /
wrong-path modes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v9.pbreed9 import ParserBreeder, pollute_sqr  # noqa: E402,F401
from v10 import planner10 as PL10                  # noqa: E402


class ParserBreeder10(ParserBreeder):
    """V0.9 gates + a path-structure cache."""

    def __init__(self):
        super().__init__()
        self.path_cache = {}       # code -> {steps, target, hits}

    # ---- path structures (class 3)
    def observe_path(self, kinds, target, steps):
        code = "|".join(sorted(set(kinds))) + ">" + str(target)
        e = self.path_cache.setdefault(
            code, {"steps": list(steps), "target": target, "hits": 0})
        e["hits"] += 1

    def path_lookup(self, kinds, target, registry):
        code = "|".join(sorted(set(kinds))) + ">" + str(target)
        e = self.path_cache.get(code)
        if not e:
            return None
        steps = [tuple(s) if isinstance(s, list) else s
                 for s in e["steps"]]
        if PL10.verify_executable(steps, kinds, registry):
            return tuple(steps)
        return None

    def save(self, path):
        super().save(path)
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        d["path_cache"] = self.path_cache
        Path(path).write_text(json.dumps(d, indent=1),
                              encoding="utf-8")

    @classmethod
    def load(cls, path):
        base = ParserBreeder.load(path)
        obj = cls()
        obj.__dict__.update(base.__dict__)
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        obj.path_cache = d.get("path_cache", {})
        return obj
