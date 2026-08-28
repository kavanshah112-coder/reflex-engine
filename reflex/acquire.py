# -*- coding: utf-8 -*-
# origin: new for V1.0 — P3 acquisition subsystem (V1_SPEC §5)
"""Acquisition: two producers (BREEDER, MINER) feeding ONE gauntlet.

Candidate lifecycle (V1_PLAN §1, frozen):
  PROPOSED -> static gates -> PROBATION -> (3 consecutive shadow
  confirmations, zero shadow wrong-fire) -> ACTIVE
  any shadow failure resets the streak; 2 resets -> REJECTED.
  Gate failure -> GATE_REJECTED. Nothing answers a live query until
  ACTIVE. Rejected candidates are logged, never deleted.

Candidate types and their injection targets (all in-place, revertible):
  lexicon_noun   {kind, noun}            -> W._EXTRA_NOUNS[kind]
  adj_map        {adj, kind}             -> W._ADJ
  unit_index     {unit, kind}            -> W._UNIT_IDX (setdefault)
  conversion     {concept, units, op, factor} -> loader canonical rules
  new_kind       {name, dim7, unit, nouns, aliases} -> KINDS tables
  new_cap        {name, inputs, output, expr} -> CAPS9-family registry
  template_struct {pattern...}           -> ParserBreeder11 deployed_struct

The LLM proposes; only the gates + shadow probation activate (I4's
proposer/validator split applied to acquisition itself). Every
candidate carries authorship metadata; ACTIVE candidates persist to
the pack's acquired.json overlay so the pack stays the auditable unit.
"""
import ast
import json
import re
import time
import uuid
from pathlib import Path

STATUSES = ("PROPOSED", "GATE_REJECTED", "PROBATION", "ACTIVE",
            "REJECTED")
N_PROBATION = 3          # frozen, V1_PLAN §1
MAX_RESETS = 2


# --------------------------------------------------------------- store
class CandidateStore:
    def __init__(self, path):
        self.path = Path(path)
        self.rows = {}
        if self.path.exists():
            for line in self.path.read_text(
                    encoding="utf-8").splitlines():
                try:
                    d = json.loads(line)
                    self.rows[d["cid"]] = d
                except Exception:
                    continue

    def add(self, ctype, payload, source, authorship=None):
        cid = f"c{uuid.uuid4().hex[:10]}"
        d = {"cid": cid, "type": ctype, "payload": payload,
             "source": source, "authorship": authorship or {},
             "status": "PROPOSED", "confirms": 0, "resets": 0,
             "history": [], "created": time.time()}
        self.rows[cid] = d
        return d

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            for d in sorted(self.rows.values(),
                            key=lambda x: x["created"]):
                f.write(json.dumps(d, default=str) + "\n")

    def by_status(self, status):
        return [d for d in self.rows.values()
                if d["status"] == status]


# --------------------------------------------- injection (apply/revert)
class Injector:
    """Apply/revert a candidate against the live engine tables.
    Revert restores the exact prior state (asserted in tests)."""

    def __init__(self):
        import v10.nlpw10 as W
        import v10.universe10 as U10
        import v9.universe9 as U9
        import v11.semrun11 as SR
        from .packs import loader
        self.W, self.U10, self.U9, self.SR = W, U10, U9, SR
        self.loader = loader

    def _rebuild_units(self):
        idx = self.W._build_unit_index()
        self.W._UNIT_IDX.clear()
        self.W._UNIT_IDX.update(idx)
        for u, ks in self.loader.UNIT_INDEX_EXTRAS.items():
            self.W._UNIT_IDX.setdefault(u, list(ks))

    def apply(self, c):
        t, p = c["type"], c["payload"]
        undo = {"type": t}
        if t == "lexicon_noun":
            lst = self.W._EXTRA_NOUNS.setdefault(p["kind"], [])
            undo["had"] = p["noun"] in lst
            if not undo["had"]:
                lst.append(p["noun"])
            undo["kind"], undo["noun"] = p["kind"], p["noun"]
        elif t == "adj_map":
            undo["prev"] = self.W._ADJ.get(p["adj"])
            undo["adj"] = p["adj"]
            self.W._ADJ[p["adj"]] = p["kind"]
        elif t == "unit_index":
            undo["prev"] = self.W._UNIT_IDX.get(p["unit"])
            undo["prev_extra"] = self.loader.UNIT_INDEX_EXTRAS.get(
                p["unit"])
            undo["unit"] = p["unit"]
            self.W._UNIT_IDX[p["unit"]] = [p["kind"]]
            self.loader.UNIT_INDEX_EXTRAS[p["unit"]] = [p["kind"]]
        elif t == "conversion":
            rules = self.SR._to_canonical.__closure__
            # canonical rules live in the loader-made closure; keep a
            # module-level side list instead:
            self.loader.EXTRA_CANONICAL.append(dict(p))
            undo["rule"] = dict(p)
        elif t == "new_kind":
            undo["name"] = p["name"]
            undo["existed"] = p["name"] in self.U10.KINDS10
            spec = (tuple(p["dim"]), p.get("unit", ""),
                    list(p.get("nouns") or []),
                    list(p.get("aliases") or []))
            self.U10.KINDS10[p["name"]] = spec
            self.W.KINDS9[p["name"]] = spec
            self._rebuild_units()
        elif t == "new_cap":
            undo["name"] = p["name"]
            undo["existed"] = p["name"] in self.SR.REG11
            spec = {"inputs": list(p["inputs"]),
                    "output": p["output"], "expr": p["expr"]}
            self.U9.CAPS9[p["name"]] = dict(spec)
            self.SR.REG11[p["name"]] = dict(spec)
        elif t == "template_struct":
            undo["key"] = p["key"]
            undo["prev"] = self.breeder_ref.deployed_struct.get(
                p["key"])
            self.breeder_ref.deployed_struct[p["key"]] = p["spec"]
        else:
            raise ValueError(f"unknown candidate type {t}")
        return undo

    def revert(self, undo):
        t = undo["type"]
        if t == "lexicon_noun":
            if not undo["had"]:
                self.W._EXTRA_NOUNS[undo["kind"]].remove(
                    undo["noun"])
                if not self.W._EXTRA_NOUNS[undo["kind"]]:
                    del self.W._EXTRA_NOUNS[undo["kind"]]
        elif t == "adj_map":
            if undo["prev"] is None:
                del self.W._ADJ[undo["adj"]]
            else:
                self.W._ADJ[undo["adj"]] = undo["prev"]
        elif t == "unit_index":
            if undo["prev"] is None:
                del self.W._UNIT_IDX[undo["unit"]]
            else:
                self.W._UNIT_IDX[undo["unit"]] = undo["prev"]
            if undo["prev_extra"] is None:
                self.loader.UNIT_INDEX_EXTRAS.pop(undo["unit"],
                                                  None)
            else:
                self.loader.UNIT_INDEX_EXTRAS[undo["unit"]] = \
                    undo["prev_extra"]
        elif t == "conversion":
            self.loader.EXTRA_CANONICAL.remove(undo["rule"])
        elif t == "new_kind":
            if not undo["existed"]:
                del self.U10.KINDS10[undo["name"]]
                del self.W.KINDS9[undo["name"]]
            self._rebuild_units()
        elif t == "new_cap":
            if not undo["existed"]:
                del self.U9.CAPS9[undo["name"]]
                del self.SR.REG11[undo["name"]]
        elif t == "template_struct":
            if undo["prev"] is None:
                del self.breeder_ref.deployed_struct[undo["key"]]
            else:
                self.breeder_ref.deployed_struct[undo["key"]] = \
                    undo["prev"]


# --------------------------------------------------------- static gates
_NOUN_RE = re.compile(r"^[a-z][a-z /-]{1,30}$")
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,30}$")


def _all_nouns(W, exclude_kind=None):
    out = {}
    for k in W.KINDS9:
        if k == exclude_kind:
            continue
        spec = W.KINDS9[k]
        for n in list(spec[2] or []):
            out[n.lower()] = k
    return out


def static_gates(c, inj):
    """Deterministic per-type checks. Returns (ok, why)."""
    W, U10, SR = inj.W, inj.U10, inj.SR
    t, p = c["type"], c["payload"]
    try:
        if t == "lexicon_noun":
            if p["kind"] not in W.KINDS9:
                return False, "kind_unknown"
            if not _NOUN_RE.match(p["noun"].lower()):
                return False, "noun_malformed"
            owner = _all_nouns(W, exclude_kind=p["kind"]).get(
                p["noun"].lower())
            if owner:
                return False, f"noun_conflict:{owner}"
            extra_owner = [k for k, v in W._EXTRA_NOUNS.items()
                           if p["noun"].lower() in
                           [x.lower() for x in v] and k != p["kind"]]
            if extra_owner:
                return False, f"noun_conflict:{extra_owner[0]}"
            own = [x.lower() for x in
                   (list(W.KINDS9[p["kind"]][2] or []) +
                    W._EXTRA_NOUNS.get(p["kind"], []))]
            if p["noun"].lower() in own:
                return False, "redundant"
            return True, "ok"
        if t == "adj_map":
            if p["kind"] not in W.KINDS9:
                return False, "kind_unknown"
            if p["adj"] in W._ADJ:
                return (False, "redundant"
                        if W._ADJ[p["adj"]] == p["kind"] else
                        f"adj_conflict:{W._ADJ[p['adj']]}")
            if not _NOUN_RE.match(p["adj"].lower()):
                return False, "adj_malformed"
            return True, "ok"
        if t == "unit_index":
            if p["kind"] not in W.KINDS9:
                return False, "kind_unknown"
            prev = W._UNIT_IDX.get(p["unit"])
            if prev is not None:
                # existing mapping: either a conflict or a redundant
                # restatement; narrowing an ambiguous entry is a
                # behavior change and needs its own future type
                return (False, "redundant" if prev == [p["kind"]]
                        else f"unit_conflict:{prev}")
            return True, "ok"
        if t == "conversion":
            if p["concept"] not in W.KINDS9:
                return False, "kind_unknown"
            f = float(p["factor"])
            if not (f > 0 and f < 1e15):
                return False, "factor_range"
            if p["op"] not in ("mul", "div"):
                return False, "op"
            return True, "ok"
        if t == "new_kind":
            if not _NAME_RE.match(p["name"]):
                return False, "name_malformed"
            if p["name"] in U10.KINDS10:
                return False, "name_exists"
            dim = p["dim"]
            if not (isinstance(dim, list) and len(dim) == 7 and
                    all(isinstance(d, int) and -4 <= d <= 4
                        for d in dim)):
                return False, "dim_malformed"
            owned = _all_nouns(W)
            for n in (p.get("nouns") or []):
                if n.lower() in owned:
                    return False, f"noun_conflict:{owned[n.lower()]}"
            # an alias that is already an indexed unit token would
            # inject ambiguity into every query using that unit (the
            # 'brick_mass aliased kg' failure from the demo)
            for a2 in (p.get("aliases") or []):
                al = str(a2).strip().lower()
                if al in W._UNIT_IDX or al in W.UNIT_WORDS:
                    return False, f"alias_unit_collision:{al}"
            u2 = str(p.get("unit") or "").strip().lower()
            if u2 and u2 in W._UNIT_IDX and len(u2) <= 3:
                return False, f"canonical_unit_collision:{u2}"
            return True, "ok"
        if t == "new_cap":
            if not _NAME_RE.match(p["name"]):
                return False, "name_malformed"
            if p["name"] in SR.REG11:
                return False, "name_exists"
            ins, out = p["inputs"], p["output"]
            if out not in U10.KINDS10 or \
                    any(i not in U10.KINDS10 for i in ins):
                return False, "kind_unknown"
            # expr must reference exactly the input kind names
            tree = ast.parse(p["expr"], mode="eval")
            names = {n.id for n in ast.walk(tree)
                     if isinstance(n, ast.Name)}
            if not names <= set(ins):
                return False, f"expr_free_vars:{sorted(names - set(ins))}"
            for node in ast.walk(tree):
                if not isinstance(node, (
                        ast.Expression, ast.BinOp, ast.UnaryOp,
                        ast.Name, ast.Constant, ast.Add, ast.Sub,
                        ast.Mult, ast.Div, ast.Pow, ast.USub,
                        ast.Load)):
                    return False, f"expr_node:{type(node).__name__}"
            # dimensional verification (count-fold rule, V0.10)
            d = _expr_dim(tree.body, {i: U10.KINDS10[i][0]
                                      for i in ins})
            if d is None:
                return False, "dim_inconsistent"
            want = U10.KINDS10[out][0]
            dz = tuple(0 if i == 5 else v for i, v in enumerate(d))
            wz = tuple(0 if i == 5 else v
                       for i, v in enumerate(want))
            if dz != wz:
                return False, f"dim_mismatch:{d}vs{want}"
            # duplicate-capability check
            for name, spec in SR.REG11.items():
                if spec.get("output") == out and \
                        sorted(spec.get("inputs") or []) == \
                        sorted(ins):
                    return False, f"duplicate_of:{name}"
            return True, "ok"
        if t == "template_struct":
            return True, "delegated_to_pbreed_gates"
        return False, "unknown_type"
    except Exception as e:
        return False, f"gate_error:{type(e).__name__}:{e}"


def _expr_dim(node, dims):
    D0 = (0,) * 7
    if isinstance(node, ast.Name):
        return dims[node.id]
    if isinstance(node, ast.Constant):
        return D0
    if isinstance(node, ast.UnaryOp):
        return _expr_dim(node.operand, dims)
    if isinstance(node, ast.BinOp):
        a = _expr_dim(node.left, dims)
        b = _expr_dim(node.right, dims)
        if a is None or b is None:
            return None
        if isinstance(node.op, (ast.Add, ast.Sub)):
            return a if a == b else None
        if isinstance(node.op, ast.Mult):
            return tuple(x + y for x, y in zip(a, b))
        if isinstance(node.op, ast.Div):
            return tuple(x - y for x, y in zip(a, b))
        if isinstance(node.op, ast.Pow):
            if isinstance(node.right, ast.Constant) and \
                    isinstance(node.right.value, (int, float)):
                return tuple(int(x * node.right.value) for x in a)
            return None
    return None


# ------------------------------------------------------------ producers
MINER_PROMPT = """You are extracting DOMAIN KNOWLEDGE from a query a \
deterministic engine could not fully handle. Do NOT solve the problem.

QUERY: {query}
{engine_report}
The engine already knows these quantity kinds (name: canonical unit):
{kinds_list}

Emit STRICT JSON only, no prose:
{{"lexicon_nouns": [{{"kind": "<existing kind name>", "noun":
"<lowercase surface word in the query that denotes that kind>"}}],
 "adj_maps": [{{"adj": "<adjective/verb in the query>", "kind":
"<existing kind>"}}],
 "unit_index": [{{"unit": "<unit token in the query>", "kind":
"<existing kind>"}}],
 "conversions": [{{"concept": "<existing kind>", "units":
["<unit>"], "op": "mul|div", "factor": <number>}}],
 "new_kinds": [{{"name": "<snake_case>", "dim": [M,L,T,I,K,N,$],
"unit": "<canonical>", "nouns": ["..."], "aliases": ["<unit alias>"]}}],
 "new_caps": [{{"name": "<snake_case>", "inputs": ["<kind>"],
"output": "<kind>", "expr": "<arithmetic over input kind names>"}}]}}

Rules: reference existing kinds by EXACT name; propose new_kinds only
if no existing kind fits; every noun/unit must literally appear in the
query; propose ONLY what fills the reported gap — do NOT restate
mappings the engine already extracted successfully; empty lists are
fine. If the ASKED-FOR quantity itself is not an existing kind,
propose it as a new_kind AND a new_cap computing it from existing
kinds. dim is exponents over [mass,length,time,current,temperature,
count,money] (e.g. speed=[0,1,-1,0,0,0,0]; money/count are the last
two). JSON only."""


class Miner:
    """LLM-driven deep-layer candidate producer (the H3 bet)."""

    def __init__(self, adapter, store):
        self.adapter = adapter
        self.store = store

    def mine(self, query, inj, engine_record=None, max_tokens=700):
        kinds_list = "\n".join(
            f"  {k}: {inj.U10.KINDS10[k][1] or '(count)'}"
            for k in sorted(inj.U10.KINDS10))
        report = ""
        if engine_record is not None:
            st = engine_record.get("_state")
            facts = []
            if st is not None:
                facts = [f"{f['concept']}={f['value']} "
                         f"{f.get('unit') or ''}".strip()
                         for f in st.facts]
            tgt = (engine_record.get("_info") or {}).get(
                "target_concept")
            report = (
                "\nENGINE REPORT (why it failed):\n"
                f"  facts it extracted: {facts or 'NONE'}\n"
                f"  target concept it identified: "
                f"{tgt or 'UNKNOWN'}\n"
                f"  failure: "
                f"{engine_record.get('abstain_reason')}\n"
                "  The gap is whatever the query mentions that the "
                "report above is missing.\n")
        prompt = MINER_PROMPT.format(query=query,
                                     engine_report=report,
                                     kinds_list=kinds_list)
        c = self.adapter.complete(prompt, max_tokens=max_tokens)
        if c.pending:
            return []
        auth = {"model": self.adapter.name,
                "tokens_in": c.tokens_in,
                "tokens_out": c.tokens_out}
        m = re.search(r"\{.*\}", c.text, re.S)
        if not m:
            return []
        try:
            j = json.loads(m.group(0))
        except Exception:
            return []
        out = []
        for key, ctype in (("lexicon_nouns", "lexicon_noun"),
                           ("adj_maps", "adj_map"),
                           ("unit_index", "unit_index"),
                           ("conversions", "conversion"),
                           ("new_kinds", "new_kind"),
                           ("new_caps", "new_cap")):
            for p in (j.get(key) or []):
                if isinstance(p, dict):
                    out.append(self.store.add(
                        ctype, p, "MINER",
                        {**auth, "query": query[:160]}))
        return out


class BreederProducer:
    """The deterministic v0.11 breeder as a producer: its deployed
    struct patterns become candidates for the shared probation."""

    def __init__(self, breeder, store):
        self.breeder = breeder
        self.store = store
        self._seen = set(breeder.deployed_struct or {})

    def observe(self, query, qid, facts, completed):
        self.breeder.observe_semantic(query, qid, facts, completed)

    def harvest(self, heldout):
        """Run the breeder's own gate battery; new deployments become
        candidates (removed from live deployment until ACTIVE)."""
        new = self.breeder.try_deploy_struct(heldout=heldout)
        out = []
        for key in list(self.breeder.deployed_struct):
            if key in self._seen:
                continue
            spec = self.breeder.deployed_struct.pop(key)
            self._seen.add(key)
            out.append(self.store.add(
                "template_struct", {"key": key, "spec": spec},
                "BREEDER", {"gates": "pbreed11_battery"}))
        return out


# ------------------------------------------------- shadow evaluation
def make_shadow_eval(engine, grade):
    """Canonical shadow evaluator (used by demo AND experiment arms):
    a shadow confirmation requires ZERO new wrong answers AND ZERO
    coverage regression (baseline-correct items that stop being
    correct). The regression clause is a P3 design decision from the
    loop-close demo: candidates that silently degrade parsing (e.g. a
    kind aliased to an existing unit) caused abstentions, which a
    wrong-answers-only check cannot see."""
    baselines = {}

    def shadow_eval(batch, cand):
        bid = id(batch)
        if bid not in baselines:
            base = {}
            for t in batch:
                r = engine.run_query(t["q"], f"shb_{t['id']}")
                v = r.get("numeric_value")
                base[t["id"]] = (v, grade(v, t.get("answer")))
            baselines[bid] = base
        base = baselines[bid]
        wrong = lost = lift = 0
        for t in batch:
            r = engine.run_query(t["q"], f"shc_{t['id']}")
            v = r.get("numeric_value")
            ok = grade(v, t.get("answer"))
            bv, bok = base[t["id"]]
            if v is not None and not ok and (bv is None or bok):
                wrong += 1
            if bok and not ok:
                lost += 1
            if ok and not bok:
                lift += 1
        return {"wrong": wrong + lost, "new_wrong": wrong,
                "lost_coverage": lost, "lift": lift}

    return shadow_eval


# ------------------------------------------------------------- gauntlet
class Gauntlet:
    """static gates -> probation (shadow batches) -> ACTIVE."""

    def __init__(self, store, injector, shadow_eval,
                 breeder=None):
        self.store = store
        self.inj = injector
        self.inj.breeder_ref = breeder
        self.shadow_eval = shadow_eval    # fn(candidates_applied) ->
        #                                   {"wrong": int, "lift": int}
        self.active_undo = {}             # cid -> undo (ACTIVE stay
        #                                   applied)

    def screen(self, cands):
        for c in cands:
            if c["status"] != "PROPOSED":
                continue
            ok, why = static_gates(c, self.inj)
            c["history"].append({"gate": why, "t": time.time()})
            c["status"] = "PROBATION" if ok else "GATE_REJECTED"
        # second pass: a new_cap rejected only for kind_unknown may
        # depend on a sibling new_kind that just entered probation —
        # re-gate with the sibling(s) tentatively applied and couple
        # them via `requires` (dependents activate only after their
        # requirements are ACTIVE)
        kinds_in_prob = {c["payload"]["name"]: c for c in cands
                         if c["type"] == "new_kind"
                         and c["status"] == "PROBATION"}
        for c in cands:
            if c["type"] != "new_cap" or \
                    c["status"] != "GATE_REJECTED" or \
                    c["history"][-1]["gate"] != "kind_unknown":
                continue
            need = [k for k in (c["payload"]["inputs"] +
                                [c["payload"]["output"]])
                    if k not in self.inj.U10.KINDS10]
            deps = [kinds_in_prob[k] for k in need
                    if k in kinds_in_prob]
            if len(deps) != len(need):
                continue
            undos = [self.inj.apply(d) for d in deps]
            try:
                ok, why = static_gates(c, self.inj)
            finally:
                for u in reversed(undos):
                    self.inj.revert(u)
            c["history"].append({"gate_with_deps": why,
                                 "t": time.time()})
            if ok:
                c["status"] = "PROBATION"
                c["requires"] = [d["cid"] for d in deps]
        self.store.save()

    def probation_round(self, shadow_batch):
        """One shadow batch over all PROBATION candidates, each
        evaluated in isolation (apply -> eval -> revert). Candidates
        with `requires` get their requirements applied for the eval;
        requirements (new_kind) are processed before dependents, so a
        coupled pair promotes in the same round."""
        results = {}
        cohort = sorted(self.store.by_status("PROBATION"),
                        key=lambda c: (c["type"] != "new_kind",
                                       c["created"]))
        for c in cohort:
            reqs = [self.store.rows[cid]
                    for cid in c.get("requires", [])]
            if any(r["status"] in ("REJECTED", "GATE_REJECTED")
                   for r in reqs):
                c["status"] = "REJECTED"
                c["history"].append({"requires_failed": True,
                                     "t": time.time()})
                results[c["cid"]] = (c["status"], None)
                continue
            dep_undos = [self.inj.apply(r) for r in reqs
                         if r["status"] != "ACTIVE"]
            undo = self.inj.apply(c)
            try:
                r = self.shadow_eval(shadow_batch, c)
            finally:
                self.inj.revert(undo)
                for u in reversed(dep_undos):
                    self.inj.revert(u)
            ok = r["wrong"] == 0
            c["history"].append({"shadow": r, "t": time.time()})
            if ok:
                c["confirms"] += 1
                if c["confirms"] >= N_PROBATION and all(
                        x["status"] == "ACTIVE" for x in reqs):
                    c["status"] = "ACTIVE"
                    self.active_undo[c["cid"]] = self.inj.apply(c)
            else:
                c["confirms"] = 0
                c["resets"] += 1
                if c["resets"] >= MAX_RESETS:
                    c["status"] = "REJECTED"
            results[c["cid"]] = (c["status"], r)
        self.store.save()
        return results

    def activate_all_active(self):
        """Re-apply ACTIVE candidates (fresh process)."""
        for c in self.store.by_status("ACTIVE"):
            if c["cid"] not in self.active_undo:
                self.active_undo[c["cid"]] = self.inj.apply(c)

    def write_overlay(self, pack_dir):
        """Persist ACTIVE candidates to the pack's acquired.json."""
        p = Path(pack_dir) / "acquired.json"
        rows = [{**{k: c[k] for k in ("cid", "type", "payload",
                                      "source", "authorship",
                                      "confirms")},
                 "requires": c.get("requires", [])}
                for c in sorted(self.store.by_status("ACTIVE"),
                                key=lambda c:
                                (c["type"] != "new_kind",
                                 c["created"]))]
        p.write_text(json.dumps(rows, indent=1), encoding="utf-8")
        return len(rows)
