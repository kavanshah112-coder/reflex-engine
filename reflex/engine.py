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
        if self.breeder is not None:
            import json as _json
            acq = Path(pack_dir) / "acquired.json"
            if acq.exists():
                for c in _json.loads(acq.read_text(
                        encoding="utf-8")):
                    if c["type"] == "template_struct":
                        self.breeder.deployed_struct[
                            c["payload"]["key"]] = \
                            c["payload"]["spec"]
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
        # acquired-kind target recovery: the vendored target-namer
        # cannot see single-word nouns of kinds added after pack load
        # (tc_hits requires multiword phrases; the v9 fallback tables
        # are import-frozen). Fires ONLY for acquired kinds and ONLY
        # when the target is unknown, so base-pack behavior and E0
        # parity are untouched by construction.
        import re as _re
        from .packs.loader import BASE_KINDS
        import v10.universe10 as _U10
        acquired = {k: _U10.KINDS10[k] for k in _U10.KINDS10
                    if k not in BASE_KINDS}
        if acquired:
            segs = [s for s in _re.split(r"[.?!]", query)
                    if s.strip()]
            askl = (segs[-1] if segs else query).lower()
            toks = set(_re.findall(r"[a-z_]+", askl))
            hits = []
            for k, spec in acquired.items():
                nouns = [k] + [n.lower() for n in (spec[2] or [])]
                for n in nouns:
                    if (" " in n and n in askl) or n in toks:
                        hits.append(k)
                        break
            tgt = info.get("target_concept")
            if len(set(hits)) == 1:
                if tgt in (None, "UNKNOWN"):
                    info["target_concept"] = hits[0]
                else:
                    # wrong-target override: the base namer picked a
                    # kind whose value is ALREADY a given input (the
                    # 'asking for what you were told' signal the arc
                    # treats as suspicious) while an acquired kind's
                    # noun literally appears in the ask
                    have = {f["concept"] for f in st.facts
                            if f.get("value") is not None}
                    if tgt in have:
                        info["target_concept"] = hits[0]
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
