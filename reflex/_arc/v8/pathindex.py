# -*- coding: utf-8 -*-
"""V0.8 Path Index + Query Index (spec Sections 9-12, 24, 34).

PathIndex: canonical registry of typed capability paths. Every canonical
path gets a deterministic PATH CODE = sha256(sorted input kinds | ordered
step names | output kind)[:12] and a stable PATH_NNN id at first
registration. Different phrasings of the same computation map to the same
code (Section 11).

kind_path_search: kind-level BFS with no-redundant-production and
round-trip (inverse-pair) rejection — the PM's own path constructor,
independent of the value planner, so duplicate-kind queries get a correct
STEP SHAPE and binding is handled separately (clause binding, pathman).

QueryIndex: persistent Q-NNNNN records + structural-signature -> path
code memoization (the repeat-query fast path, H4).
"""
import hashlib
import json
import re
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v8.recognize8 import path_is_roundtrip     # noqa: E402


def path_code(input_kinds, steps, output_kind):
    doc = json.dumps([sorted(input_kinds), list(steps), output_kind])
    return hashlib.sha256(doc.encode()).hexdigest()[:12]


class PathIndex:
    def __init__(self):
        self.by_code = {}
        self.next_id = 1
        self.hits = 0
        self.misses = 0

    def register(self, input_kinds, steps, output_kind, validated=False):
        code = path_code(input_kinds, steps, output_kind)
        rec = self.by_code.get(code)
        if rec is None:
            rec = {"path_id": f"PATH_{self.next_id:03d}", "code": code,
                   "input_kinds": sorted(set(input_kinds)),
                   "steps": list(steps), "output_kind": output_kind,
                   "uses": 0, "validated": bool(validated)}
            self.by_code[code] = rec
            self.next_id += 1
        rec["uses"] += 1
        if validated:
            rec["validated"] = True
        return rec

    def lookup(self, code):
        rec = self.by_code.get(code)
        if rec is not None:
            self.hits += 1
        else:
            self.misses += 1
        return rec

    def save(self, path):
        Path(path).write_text(json.dumps(
            {"next_id": self.next_id,
             "paths": list(self.by_code.values())}, indent=1),
            encoding="utf-8")

    @classmethod
    def load(cls, path):
        pi = cls()
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        pi.next_id = d["next_id"]
        for rec in d["paths"]:
            pi.by_code[rec["code"]] = rec
        return pi

    def registry_hash(self):
        slim = sorted((r["code"], r["path_id"], tuple(r["steps"]))
                      for r in self.by_code.values())
        return hashlib.sha256(json.dumps(slim).encode()).hexdigest()


def build_links(registry):
    """Typed reflex-to-reflex links: output kind -> capabilities that can
    consume it (Section 24). Used ONLY to prune search (ablation N/O)."""
    links = {}
    for name, spec in registry.items():
        for k in spec["inputs"]:
            links.setdefault(k, []).append(name)
    return links


def kind_path_search(kinds, target, registry, use_links=True, links=None,
                     max_depth=5, budget=400):
    """Kind-level BFS toward target. Returns (steps or None, stats).
    States are frozensets of AVAILABLE kinds (set semantics — value
    binding and multiplicity are the executor's job)."""
    have = frozenset(kinds)
    stats = {"expansions": 0}
    if links is None and use_links:
        links = build_links(registry)
    goals = {target}
    if target == "money":
        from v4.partial_planner import MONEY_GROUP
        goals = set(MONEY_GROUP)
    if have & goals:
        pass  # target may already be present; still allow 0-step? No —
        # a query asking for a given quantity is degenerate; search on.
    q = deque([(have, ())])
    seen = {have}
    found = []
    while q and stats["expansions"] < budget and len(found) < 14:
        state, steps = q.popleft()
        if len(steps) > max_depth:
            continue
        # candidate caps: via links (only caps consuming an available
        # kind) or full scan
        if use_links:
            cand = {n for k in state for n in links.get(k, [])}
        else:
            cand = set(registry)
        for name in sorted(cand):
            spec = registry[name]
            if spec.get("transfer") or name in steps:
                continue
            if not all(k in state for k in spec["inputs"]):
                continue
            out = spec["output"]
            if out in state and out not in goals:
                continue   # no-redundant-production
            stats["expansions"] += 1
            nsteps = steps + (name,)
            if path_is_roundtrip(nsteps, registry):
                continue
            nstate = state | {out}
            if out in goals:
                # no dangling intermediates: every earlier step's output
                # must be consumed by a later step (else the path did
                # spurious work — classic junk-consumption trap)
                ok_chain = True
                for i2, n2 in enumerate(nsteps[:-1]):
                    o2 = registry[n2]["output"]
                    if not any(o2 in registry[n3]["inputs"]
                               for n3 in nsteps[i2 + 1:]):
                        ok_chain = False
                        break
                if ok_chain:
                    found.append(nsteps)
                continue
            if nstate not in seen:
                seen.add(nstate)
                q.append((nstate, nsteps))
    if not found:
        return None, stats
    def score(steps):
        used = set()
        for n in steps:
            used |= set(registry[n]["inputs"])
        distinct = len(used & have)
        return (-distinct, len(steps))
    found.sort(key=score)
    best = found[0]
    # ambiguity: another path with the SAME score but a DIFFERENT step
    # set is a genuinely different computation (KE vs PE for 'energy')
    for alt in found[1:]:
        if score(alt) == score(best) and set(alt) != set(best):
            stats["ambiguous"] = [list(best), list(alt)]
            return None, stats
    return list(best), stats


class QueryIndex:
    def __init__(self):
        self.records = {}
        self.next_id = 1
        self.sig_memo = {}      # structural signature -> path code

    def new(self, query, fingerprint_sig, target, qid_hint=None):
        # deterministic id when the caller provides a stable item id —
        # REQUIRED for deferred-replay resumability (bug audit B2): a
        # sequential counter gives the same item different Q-ids across
        # passes, changing the prompt sha and defeating the cache
        if qid_hint:
            qid = f"Q-{qid_hint}"
            if qid in self.records:
                return qid
        else:
            qid = f"Q-{self.next_id:05d}"
            self.next_id += 1
        self.records[qid] = {
            "query_index": qid, "original_query": query,
            "signature": fingerprint_sig, "target": target,
            "candidate_paths": [], "selected_path": None,
            "current_step": 0, "completed_steps": [],
            "state": [], "unresolved": [], "validation_status": None,
            "final_result": None,
        }
        return qid

    def memo_get(self, sig):
        return self.sig_memo.get(sig)

    def memo_put(self, sig, code):
        self.sig_memo[sig] = code

    def save(self, path):
        Path(path).write_text(json.dumps(
            {"next_id": self.next_id, "sig_memo": self.sig_memo},
            indent=0), encoding="utf-8")


# ------------------------------------------------------ clause binding
_CLAUSE_SPLIT = re.compile(r"[.;]")
_NUM_FIND = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


def clause_of_value(text, value):
    """Index of the first clause containing the (raw) number, else -1."""
    for i, cl in enumerate(_CLAUSE_SPLIT.split(text)):
        for m in _NUM_FIND.finditer(cl):
            try:
                v = float(m.group(0).replace(",", ""))
            except ValueError:
                continue
            if abs(v - value) < 1e-9:
                return i
            # unit-converted values (min->s etc.): match raw digits too
    return -1


def tag_clauses(text, qs):
    """Clause tag per quantity (value or common back-conversions)."""
    tags = []
    for q in qs:
        c = clause_of_value(text, q.value)
        if c < 0:
            for f in (60.0, 3600.0, 1e-3, 1e3, 100.0, 0.01, 3.6,
                      1 / 3.6, 3.6e6, 1e6, 1e-6, 1e-2, 1e2):
                c = clause_of_value(text, q.value / f)
                if c >= 0:
                    break
        tags.append(c)
    return tags
