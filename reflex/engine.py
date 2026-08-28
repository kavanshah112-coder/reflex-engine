# -*- coding: utf-8 -*-
# origin: new for V1.0 — pack-driven engine core (V1_SPEC §3)
"""The integrated reflex engine: pack-driven C10-configuration
pipeline (parse -> breeder augmentation -> certify -> execute), the
exact champion recipe from v11/run11.run_control, with every domain
table supplied by a domain pack instead of hardcoded state.

boot() once per process (one pack per process — the in-place
injection pattern the arc always used).
"""
import sys
import time
from pathlib import Path

_ARC = Path(__file__).resolve().parent / "_arc"
if str(_ARC) not in sys.path:
    sys.path.insert(0, str(_ARC))

from .packs import loader                                  # noqa: E402

DEFAULT_PACK = Path(__file__).resolve().parents[1] / "packs" / \
    "physics"


class Engine:
    def __init__(self, pack_dir=DEFAULT_PACK, resolver=None,
                 redundancy=True, use_breeder=True):
        loader.apply(pack_dir)
        from v11.semparse11 import parse as _parse
        from v11.integrity11 import certify as _certify
        from v11.semrun11 import run as _run
        self._parse, self._certify, self._run = (_parse, _certify,
                                                 _run)
        self.breeder = (loader.load_breeder(pack_dir)
                        if use_breeder else None)
        self.resolver = resolver
        self.redundancy = redundancy
        self.pack_dir = str(pack_dir)

    def run_query(self, query, qid, available=None):
        """One query through the full pipeline. Returns the v11-style
        record + parse artifacts (facts/state for certificates)."""
        t0 = time.perf_counter()
        rec = {"query_id": qid, "llm_calls": [],
               "reflex_parse": False}
        tp = time.perf_counter()
        st, info = self._parse(query, qid)
        rec["parse_ms"] = (time.perf_counter() - tp) * 1e3
        if self.breeder is not None:
            extra = self.breeder.extract_struct(query)
            known_unknown = [f for f in st.facts
                             if f["concept"] in (None, "UNKNOWN")]
            for (c, v, u) in extra:
                for f in known_unknown:
                    if f["value"] is not None and \
                            abs(f["value"] - v) < 1e-9:
                        f["concept"] = c
                        rec["reflex_parse"] = True
        ti = time.perf_counter()
        self._certify(st)
        rec["integrity_ms"] = (time.perf_counter() - ti) * 1e3
        r = self._run(st, info, query, qid, use_llm=False,
                      resolver=self.resolver,
                      redundancy=self.redundancy, avail=available)
        rec.update({k: r.get(k) for k in
                    ("status", "numeric_value", "abstain_reason",
                     "mode", "resolver_used", "redundancy_checked",
                     "invariant_violations")})
        rec["llm_calls"] = r.get("llm_calls", [])
        rec["t_ms"] = (time.perf_counter() - t0) * 1e3
        rec["_state"] = st
        rec["_info"] = info
        return rec
