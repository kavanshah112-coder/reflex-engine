# -*- coding: utf-8 -*-
"""V1.10 gateway: exact library -> SUGGEST (own-answer filtered) -> escalate.

  python tools/engine110.py sample  --split acq|dev|seal|replay     # E-SAMPLE + batch files (no golds)
  python tools/engine110.py run     --arm det|sonnet|opus|haiku|fable --split acq|dev|seal|replay [--checkpoint 20000]
  python tools/engine110.py tokens                                  # TOKENS/QUERY from bridge/usage.jsonl
  python tools/engine110.py controls

Paths per item (V110_SPEC §4.1):
  EXACT   V1.6 packs (ask16) + V1.6 reflex library + composer17 chains + binder18 role
          skeletons (planlib18_all_all + arm-minted P templates) + exact L2-skeleton
          readings whose probation cleared  -> CERTIFIED, model-free
  SUGGEST every admitted reading on the cue key (Z-SLOT, S-MULTI applied), executed;
          A2S = passes arm gates AND agrees with the model's own answer (needs the
          answer -> sample items only); A0S reported; KC shadow (>=3 donors agree)
  FRESH   proposer reading on the sample -> A2 -> library (probation)
  ESCALATE otherwise (LLM_ESCALATED, uncertified; graded for the LLM-only baseline)
Arm gates: G-P6 is a RULE on haiku, REPORTED on sonnet/opus/fable (frozen §11.5).
"""
import argparse
import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tools"))
import reader19 as S1  # noqa: E402
import reader19v as V  # noqa: E402
from reflex import planschema17 as PS  # noqa: E402

OUT = HERE / "results" / "v110"
DATA = OUT / "data"
BRIDGE = OUT / "bridge"
MODELS = ["sonnet", "opus", "haiku", "fable"]
G6_RULE = {"haiku": True, "sonnet": False, "opus": False, "fable": False, "det": False}
TIERS = ["T1", "T2", "T3", "T3p", "T4", "P1", "P2", "P3", "P4", "PC", "D"]
P_TIERS = {"P1", "P2", "P3", "P4"}
SAMPLE_QUOTA = {
    "acq": {"T1": 300, "T2": 400, "T3": 800, "T3p": 250, "T4": 500, "P1": 300, "P2": 300, "P3": 300, "P4": 400, "PC": 250, "D": 200},
    "dev": {"T1": 100, "T2": 100, "T3": 300, "T3p": 100, "T4": 150, "P1": 100, "P2": 100, "P3": 100, "P4": 150, "PC": 100, "D": 50},
    "seal": {"T1": 200, "T2": 250, "T3": 600, "T3p": 250, "T4": 400, "P1": 200, "P2": 250, "P3": 250, "P4": 300, "PC": 250, "D": 100},
    "replay": {"T1": 50, "T2": 50, "T3": 250, "T3p": 100, "T4": 150, "P1": 50, "P2": 50, "P3": 50, "P4": 150, "PC": 250, "D": 50},
}
PROBATION_SERVES, PROBATION_TUPLES = 3, 3
S_MULTI = re.compile(
    r"\b(how (?:much|many|long|old)\b[^.?]*\b(?:did|do|had|has|have|was|were) each\b(?![^.?]*\b(?:get|receive|equally))|"
    r"each cost|how long are the pieces|find (?:their|the) (?:present )?ages|the ages of|"
    r"respectively\?|plus extra|both numbers|find the (?:two|three) numbers|"
    r"what are the (?:two|three|numbers|dimensions|lengths|ages))", re.I)


# ---------------------------------------------------------------- data


def h(s):
    return hashlib.sha1(s.encode()).hexdigest()


def load_split(split, with_text_only=True):
    out = []
    with open(DATA / ("w400k_%s.jsonl" % split), encoding="utf-8") as f:
        for line in f:
            it = json.loads(line)
            if with_text_only and not it.get("text"):
                continue
            out.append(it)
    return out


def sample_ids(split):
    """hashed, tier-stratified E-SAMPLE (same for every arm)."""
    items = load_split(split)
    by_tier = defaultdict(list)
    for it in items:
        by_tier[it["tier"]].append(it)
    chosen = []
    for tier, q in SAMPLE_QUOTA[split].items():
        pool = sorted(by_tier.get(tier, []), key=lambda it: h("sample:" + it["id"]))
        chosen.extend(pool[:q])
    return chosen


def load_answers(model, split):
    out = {}
    for p in BRIDGE.glob("ans_%s_%s_*.json" % (model, split)):
        try:
            out.update(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out


def load_readings(model, split):
    out = {}
    d = BRIDGE / ("read_%s_%s" % (model, split))
    if not d.exists():
        return out
    for p in d.glob("reading_*.json"):
        iid = p.stem[len("reading_"):]
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            out[iid] = "FORMAT"
            continue
        out[iid] = r if isinstance(r, dict) and set(r) == {"plan"} else "FORMAT"
    return out


def parse_own(item, s):
    if item["gold_type"] == "mc":
        m = re.search(r"\b([ABCD])\b", str(s or "").upper())
        return m.group(1) if m else None
    return S1.parse_answer(s)


def grade(item, value):
    if item.get("distractor") or item["gold_type"] == "none":
        return False
    if item["gold_type"] == "mc":
        return value == item["gold"]
    return S1.close(value, S1.parse_answer(item["gold"]))


# ---------------------------------------------------------------- library (per arm)


class Lib(object):
    """T: admitted readings; P: binder18 templates minted by this arm."""

    def __init__(self):
        self.T = []            # {donor, key, skel, plan, sig, donors, serves, tuples, wrong}
        self.by_key = defaultdict(list)
        self.by_skel = defaultdict(list)
        self.P = []            # harvest18 templates
        self.sig_index = {}

    def add_T(self, donor, key, skel, plan, sig, minted_by):
        for t in self.by_key.get(key, []):
            if t["sig"] == sig:
                t["donors"].add(donor)
                return t
        t = {"donor": donor, "key": key, "skel": skel, "plan": plan, "sig": sig,
             "donors": {donor}, "serves": 0, "tuples": set(), "wrong": 0, "minted_by": minted_by}
        self.T.append(t)
        self.by_key[key].append(t)
        self.by_skel[skel].append(t)
        return t

    def probated(self, t):
        return t["serves"] >= PROBATION_SERVES and len(t["tuples"]) >= PROBATION_TUPLES and t["wrong"] == 0 and len(t["donors"]) >= 2

    def dump(self, path):
        json.dump({"T": [dict(t, donors=sorted(t["donors"]), tuples=sorted(t["tuples"])) for t in self.T],
                   "P": self.P}, open(path, "w", encoding="utf-8"))

    @classmethod
    def load(cls, path):
        L = cls()
        if not Path(path).exists():
            return L
        d = json.load(open(path, encoding="utf-8"))
        for t in d["T"]:
            tt = L.add_T(t["donor"], t["key"], t["skel"], t["plan"], t["sig"], t.get("minted_by", "?"))
            tt["donors"] = set(t["donors"]); tt["serves"] = t["serves"]; tt["tuples"] = set(t["tuples"]); tt["wrong"] = t["wrong"]
        L.P = d.get("P", [])
        return L


def seed_library_from_v19(model):
    """the arm's own V1.9/S1 admitted readings (burned data) as the starting T library."""
    L = Lib()
    v19 = HERE / "results" / "v19"
    for phase in ("dev", "sealed"):
        rp = v19 / ("M-%s_%s_rows.json" % (model, phase))
        if not rp.exists():
            continue
        rows = json.loads(rp.read_text(encoding="utf-8"))
        items = {it["id"]: it for it in V._load_items(phase)}
        readings = V._load_readings(model, phase)
        for r in rows:
            if not r.get("A2"):
                continue
            it = items[r["id"]]
            plan = readings[r["id"]]["plan"]
            bound, _ = S1.bind(plan, it["numbers"])
            L.add_T(r["id"], r["key"], S1.skeleton(it["text"], 2), plan, PS.signature(bound), "v19")
    return L


# ---------------------------------------------------------------- exact path (V1.6 + V1.8 + probated readings)

_EX = {}


def _boot_exact():
    if _EX:
        return _EX
    from reflex import acquire16, binder18, chainexec17, composer17, plangate18, roles18
    from reflex.gateway16 import ask16
    lib_p = binder18.Library.load([str(HERE / "results" / "v18" / "planlib18_all_all.json")])
    reflexlib = json.loads((HERE / "results" / "v16" / "reflexlib_all.json").read_text(encoding="utf-8"))
    _EX.update(dict(ask16=ask16, acquire16=acquire16, binder18=binder18, chainexec17=chainexec17,
                    composer17=composer17, plangate18=plangate18, roles18=roles18, lib_p=lib_p, reflexlib=reflexlib))
    _EX["CHAIN"] = re.compile(r"\b(?:this|that|the) result\b|\bas (?:a |the )?(?:principal|speed|mass|acceleration|force|distance|height|voltage|current|resistance|v|p|m|a)\b|\b(?:multiply|divide|add|subtract|increase|decrease|express|convert)\b[^.]*\b(?:that|it|the result)\b|\bwith (?:this|it|that)\b|from this\b|using (?:this|that|it)\b|then\b", re.I)
    return _EX


def exact(item, lib):
    """-> (value, path) or (None, reason). Model-free."""
    E = _boot_exact()
    text = item["text"]
    try:
        chainish = bool(E["CHAIN"].search(text)) or text.count(". ") >= 2
        if not chainish:
            r = E["ask16"](text, item["id"])
            if r["status"] == "SERVED":
                return r["value"], "exact:v16:" + r["path"]
            if r["status"] == "ESCALATED":
                hit = E["acquire16"].apply_library(text, E["reflexlib"])
                if hit is not None:
                    return hit["value"], "exact:v16:reflex"
        plan = E["composer17"].parse_chain(text)
        roles = E["roles18"].analyze(text)
        if plan is not None:
            ok, tr = E["plangate18"].check(plan, text, roles)
            if ok:
                v, cert = E["chainexec17"].run(plan)
                if v is not None:
                    return v, "exact:chain:composer"
        v, cert, info = E["binder18"].serve(text, E["lib_p"], qid=item["id"], roles=roles)
        if v is not None:
            return v, "exact:bind18:" + str(info["template"])
        if lib.P:
            v, cert, info = E["binder18"].serve(text, E["binder18"].Library(lib.P), qid=item["id"], roles=roles)
            if v is not None:
                return v, "exact:bindP:" + str(info["template"])
    except Exception as exc:  # noqa: BLE001
        return None, "engine-error:%s" % type(exc).__name__
    # probated readings on the exact L2 skeleton
    skel = S1.skeleton(text, 2)
    cands = [t for t in lib.by_skel.get(skel, []) if lib.probated(t) and item["id"] not in t["donors"]]
    if cands:
        vals = set()
        for t in cands:
            row = V.stage(item, {"plan": t["plan"]})
            if row["status"] == "executed" and row["g6"] and not row["rule"]:
                vals.add(round(row["value"], 9))
        if len(vals) == 1:
            return vals.pop(), "exact:reading:" + skel[:30]
        if len(vals) > 1:
            return None, "reading_collision"
    return None, "no_exact"


# ---------------------------------------------------------------- suggest / fresh


def gates_pass(row, arm):
    return (row["g6"] or not G6_RULE.get(arm, False)) and not row["rule"]


def suggest(item, lib, own, arm):
    """-> dict(A0S, A2S, KC, value, donor, sig, n_cands, executed, agree_sigs)."""
    res = {"n_cands": 0, "executed": 0, "A0S": None, "A2S": None, "KC": None}
    if not item.get("numbers"):
        res["skip"] = "Z-SLOT"
        return res
    if S_MULTI.search(item["text"]):
        res["skip"] = "S-MULTI"
        return res
    cands = [t for t in lib.by_key.get(item["key"], []) if item["id"] not in t["donors"] and len(re.findall(r"\{n\d+\}", json.dumps(t["plan"]))) > 0]
    res["n_cands"] = len(cands)
    if not cands:
        return res
    vals = []
    for t in cands:
        row = V.stage(item, {"plan": t["plan"]})
        if row["status"] != "executed":
            continue
        res["executed"] += 1
        vals.append((row["value"], t, gates_pass(row, arm)))
    if not vals:
        return res
    # KC shadow: >=3 distinct donors' readings all agree
    if len({id(t) for _v, t, _g in vals}) >= 3:
        vs = [v for v, _t, _g in vals]
        if all(S1.close(v, vs[0]) for v in vs):
            res["KC"] = vs[0]
    if own is None:
        return res
    for v, t, g in vals:
        if S1.close(v, own):
            if res["A0S"] is None:
                res["A0S"] = (v, t)
            if g:
                res["A2S"] = (v, t)
                break
    return res


def fresh(item, reading, own, arm):
    if reading is None or reading == "FORMAT":
        return {"status": "format" if reading == "FORMAT" else "missing"}
    if item.get("tier") in P_TIERS:
        return fresh_P(item, reading, own, arm)
    row = V.stage(item, reading)
    if row["status"] != "executed":
        return row
    row["agree"] = own is not None and S1.close(row["value"], own)
    row["A2"] = bool(row["agree"] and gates_pass(row, arm) and item.get("numbers") and not S_MULTI.search(item["text"]))
    if row["A2"]:
        bound, _ = S1.bind(reading["plan"], item["numbers"])
        row["sig"] = PS.signature(bound)
    return row


def fresh_P(item, reading, own, arm):
    """physics reading = V1.7 chain plan with literal values; gated by plangate18 with roles."""
    E = _boot_exact()
    plan = reading.get("plan")
    if not isinstance(plan, dict) or "nodes" not in plan:
        return {"status": "format"}
    try:
        roles = E["roles18"].analyze(item["text"])
        ok, tr = E["plangate18"].check(plan, item["text"], roles)
        if not ok:
            return {"status": "gate_kill", "gate": tr[-1].get("gate")}
        v, cert = E["chainexec17"].run(plan)
    except Exception as exc:  # noqa: BLE001
        return {"status": "exec_error", "reason": repr(exc)[:60]}
    if v is None:
        return {"status": "exec_refused"}
    row = {"status": "executed", "value": v, "g6": True, "rule": None}
    row["agree"] = own is not None and S1.close(v, own)
    row["A2"] = bool(row["agree"])
    if row["A2"]:
        row["sig"] = PS.signature(plan)
        try:
            import harvest18 as H18
            tpl, why = H18.templateize(item["text"], plan)
            row["template"] = tpl
        except Exception:  # noqa: BLE001
            row["template"] = None
    return row


# ---------------------------------------------------------------- run


def run(arm, split, checkpoint=0, lib_in=None, lib_out=None, limit=0, tiers=None, tag=""):
    items = load_split(split)
    if tiers:
        items = [it for it in items if it["tier"] in tiers]
    if limit:
        items = items[:limit]
    sample = {it["id"] for it in sample_ids(split)}
    answers = load_answers(arm, split) if arm != "det" else {}
    readings = load_readings(arm, split) if arm != "det" else {}
    lib = Lib.load(lib_in) if lib_in else (seed_library_from_v19(arm) if arm != "det" else Lib())
    st = Counter()
    by_tier = defaultdict(Counter)
    rows, wrongs, curve = [], [], []
    t0 = time.perf_counter()
    for n, it in enumerate(items):
        tier = it["tier"]
        rec = {"id": it["id"], "tier": tier, "sampled": it["id"] in sample}
        by_tier[tier]["n"] += 1
        # exclude items this arm's model authored from SEAL/REPLAY scoring
        if it.get("author_model") == arm and split in ("seal", "replay"):
            rec["excluded_author"] = True
            by_tier[tier]["excluded_author"] += 1
            rows.append(rec)
            continue
        own = parse_own(it, answers.get(it["id"])) if it["id"] in sample else None
        rec["own"] = own
        if own is not None:
            by_tier[tier]["own_answered"] += 1
            ok_own = grade(it, own)
            by_tier[tier]["own_correct"] += ok_own
            rec["own_correct"] = ok_own
        # 1. exact
        v, path = exact(it, lib)
        if v is not None and it["gold_type"] != "mc":
            rec.update(path=path, value=v)
            ok = grade(it, v)
            rec["correct"] = ok
            by_tier[tier]["exact_served"] += 1
            by_tier[tier]["exact_correct" if ok else "exact_WRONG"] += 1
            if it.get("distractor"):
                by_tier[tier]["SAFETY2"] += 1
            if not ok:
                wrongs.append(dict(rec, gold=it["gold"], text=it["text"][:160]))
            rows.append(rec)
            continue
        if v is not None:  # PC item got a value from the exact path = SAFETY-PC
            by_tier[tier]["SAFETY_PC"] += 1
            rec["safety_pc"] = path
        rec["exact_reason"] = path
        # 2. suggest (needs own answer; KC shadow regardless)
        sg = suggest(it, lib, own, arm) if it["gold_type"] == "num" and not it.get("distractor") else {"n_cands": 0, "executed": 0, "A0S": None, "A2S": None, "KC": None}
        rec["n_cands"] = sg["n_cands"]
        if sg.get("KC") is not None:
            by_tier[tier]["KC_served"] += 1
            by_tier[tier]["KC_correct" if grade(it, sg["KC"]) else "KC_WRONG"] += 1
        for rule in ("A0S", "A2S"):
            if sg.get(rule) is not None:
                vv, t = sg[rule]
                ok = grade(it, vv)
                by_tier[tier][rule + "_served"] += 1
                by_tier[tier][rule + ("_correct" if ok else "_WRONG")] += 1
                if rule == "A2S":
                    rec.update(path="suggest:" + t["donor"], value=vv, correct=ok, donor=t["donor"])
                    t["serves"] += 1
                    t["tuples"].add(json.dumps(it["numbers"], sort_keys=True))
                    if not ok:
                        t["wrong"] += 1
                        wrongs.append(dict(rec, gold=it["gold"], text=it["text"][:160], rule="A2S"))
        # 3. fresh reading (sample with proposer)
        rd = readings.get(it["id"])
        if rd is not None and it["gold_type"] == "num" and not it.get("distractor"):
            fr = fresh(it, rd, own, arm)
            rec["fresh"] = fr.get("status")
            by_tier[tier]["fresh_" + fr.get("status", "?")] += 1
            if fr.get("status") == "executed":
                okr = grade(it, fr["value"])
                by_tier[tier]["fresh_reading_correct"] += okr
                if fr.get("A2"):
                    by_tier[tier]["A2_admitted"] += 1
                    by_tier[tier]["A2_correct" if okr else "A2_WRONG"] += 1
                    if not okr:
                        wrongs.append(dict(rec, gold=it["gold"], text=it["text"][:160], rule="A2", value=fr["value"]))
                    if rec.get("path") is None:
                        rec.update(path="fresh", value=fr["value"], correct=okr)
                    # mint (fresh A2 always mints its own donor; suggested hit mints on plan agreement)
                    if tier in P_TIERS:
                        if fr.get("template"):
                            tpl = dict(fr["template"]); tpl.setdefault("donors", [it["id"]]); tpl["name"] = "P-%s" % it["id"]
                            lib.P.append(tpl)
                    else:
                        t = lib.add_T(it["id"], it["key"], S1.skeleton(it["text"], 2), rd["plan"], fr["sig"], arm)
                        t["serves"] += 1; t["tuples"].add(json.dumps(it["numbers"], sort_keys=True))
                        if sg.get("A2S") is not None:
                            vv, ts = sg["A2S"]
                            bound, _ = S1.bind(ts["plan"], it["numbers"])
                            if PS.signature(bound) == fr["sig"]:
                                ts["donors"].add(it["id"])
                                by_tier[tier]["plan_agree"] += 1
                            else:
                                by_tier[tier]["plan_disagree"] += 1
        if rec.get("path") is None:
            by_tier[tier]["escalated"] += 1
            rec["path"] = "escalate"
        rows.append(rec)
        if checkpoint and (n + 1) % checkpoint == 0:
            curve.append({"n": n + 1, "library_T": len(lib.T), "library_P": len(lib.P),
                          "A2S_served": sum(c["A2S_served"] for c in by_tier.values()),
                          "exact_served": sum(c["exact_served"] for c in by_tier.values())})
    wall = time.perf_counter() - t0
    summ = {"arm": arm, "split": split, "n": len(items), "sampled": len(sample), "ms_per_query": round(1000 * wall / max(1, len(items)), 3),
            "library_T": len(lib.T), "library_P": len(lib.P), "probated_T": sum(1 for t in lib.T if lib.probated(t)),
            "by_tier": {k: dict(v) for k, v in sorted(by_tier.items())}, "curve": curve,
            "totals": {k: sum(c[k] for c in by_tier.values()) for k in
                       ["n", "exact_served", "exact_WRONG", "A2S_served", "A2S_WRONG", "A0S_served", "A0S_WRONG", "KC_served", "KC_WRONG",
                        "A2_admitted", "A2_WRONG", "escalated", "own_answered", "own_correct", "SAFETY_PC", "SAFETY2", "excluded_author"]}}
    OUT.mkdir(parents=True, exist_ok=True)
    base = OUT / ("%s_%s%s" % (arm, split, ("_" + tag) if tag else ""))
    (Path(str(base) + "_summary.json")).write_text(json.dumps(summ, indent=1), encoding="utf-8")
    (Path(str(base) + "_wrong.json")).write_text(json.dumps(wrongs, indent=1, default=str), encoding="utf-8")
    with open(str(base) + "_rows.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    if lib_out:
        lib.dump(lib_out)
    print(json.dumps({k: v for k, v in summ.items() if k not in ("by_tier", "curve")}, indent=1))
    return summ


# ---------------------------------------------------------------- sample batches (no golds)

P_OPS_DOC = ("Plan node ops (V1.7 chain language; every number you use must appear in the question): "
             "{'op':'formula','expr':'<python expr over named inputs>', '<input>': <number or '@n<k>'>, 'unit':'<answer unit>'}, "
             "{'op':'evaluate','expr':'<expr with @n<k> refs and literals>'}, {'op':'scale','value':'@n<k>','by':<number>}, "
             "{'op':'convert','value':'@n<k>','from':'<unit>','to':'<unit>'}. Physical constants: g = 9.8 only.")


def write_batches(split, tiers=None):
    """batch files per tier: ansq_<split>_<tier>_NNN.json / readq_<split>_<tier>_NNN.json (no golds)."""
    chosen = sample_ids(split)
    if tiers:
        chosen = [it for it in chosen if it["tier"] in tiers]
    BRIDGE.mkdir(parents=True, exist_ok=True)
    by_tier = defaultdict(lambda: ([], []))
    for it in chosen:
        by_tier[it["tier"]][0].append({"id": it["id"], "question": it["text"]})
        if it["gold_type"] == "num" and not it.get("distractor"):
            e = {"id": it["id"], "question": it["text"], "numbers": it["numbers"]}
            if it["tier"] in P_TIERS:
                e["reading_language"] = "chain"
                e["kind_hint"] = it.get("leaves")
            else:
                e["reading_language"] = "slots"
            by_tier[it["tier"]][1].append(e)
    nb = Counter()
    for tier, (ans, rd) in by_tier.items():
        for name, lst in (("ansq", ans), ("readq", rd)):
            for bi in range(0, len(lst), 25):
                (BRIDGE / ("%s_%s_%s_%03d.json" % (name, split, tier, bi // 25))).write_text(json.dumps(lst[bi:bi + 25], indent=0), encoding="utf-8")
                nb[name + "_" + tier] += 1
    man_p = OUT / ("sample_%s.json" % split)
    man = json.loads(man_p.read_text(encoding="utf-8")) if man_p.exists() else {"split": split, "tiers": {}}
    for tier in by_tier:
        man["tiers"][tier] = {"items": len(by_tier[tier][0]), "answer_batches": nb["ansq_" + tier], "reading_batches": nb["readq_" + tier],
                              "sha256_ids": hashlib.sha256(chr(10).join(sorted(x["id"] for x in by_tier[tier][0])).encode()).hexdigest()}
    man_p.write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(json.dumps(man, indent=1))


# ---------------------------------------------------------------- tokens


def tokens():
    """bridge/usage.jsonl rows: {agent, model, role, split, items, subagent_tokens, tool_uses, duration_ms}"""
    p = BRIDGE / "usage.jsonl"
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []
    agg = defaultdict(lambda: Counter())
    for r in rows:
        k = (r["model"], r["role"], r["split"])
        agg[k]["items"] += r["items"]; agg[k]["tokens"] += r["subagent_tokens"]; agg[k]["agents"] += 1
    out = {"%s|%s|%s" % k: {"items": v["items"], "tokens": v["tokens"], "agents": v["agents"],
                             "tokens_per_item": round(v["tokens"] / v["items"], 1) if v["items"] else None} for k, v in agg.items()}
    (OUT / "tokens110.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


# ---------------------------------------------------------------- controls


def controls():
    res = {}
    res["v19_batteries"] = bool(json.loads((HERE / "results" / "v19" / "controls19v.json").read_text(encoding="utf-8")).get("pass"))
    # Z-SLOT: a zero-number item must get no candidates
    L = Lib(); L.add_T("d1", "count|0|", "x", {"nodes": [{"id": "n1", "op": "evaluate", "expr": "6"}], "final": "n1"}, "s", "ctl")
    it0 = {"id": "x1", "text": "Faye scored twenty-eight points and everyone else eight each. How many players?", "numbers": {}, "key": "count|0|", "gold_type": "num", "gold": "5"}
    res["Z-SLOT"] = suggest(it0, L, 6.0, "sonnet").get("skip") == "Z-SLOT"
    # S-MULTI positive and negative
    res["S-MULTI_pos"] = bool(S_MULTI.search("A bicycle and a helmet cost 240 dollars. How much did each cost, if the bicycle cost 5 times as much?"))
    res["S-MULTI_pos2"] = bool(S_MULTI.search("Find the present ages of father and son."))
    res["S-MULTI_neg"] = not S_MULTI.search("Ann shares 24 apples equally among 4 friends. How many apples does each of the friends get?")
    # suggest positive: a same-key donor reading must serve when it agrees with the own answer
    L2 = Lib()
    L2.add_T("d2", "count|2|bare,bare", "x", {"nodes": [{"id": "n1", "op": "evaluate", "expr": "{n0}+{n1}"}], "final": "n1"}, "s", "ctl")
    it1 = {"id": "x2", "text": "Ben has 12 marbles and Kira has 7 marbles. How many marbles do they have together?", "numbers": {"n0": "12", "n1": "7"}, "gold_type": "num", "gold": "19"}
    it1["key"] = V.cue_key(it1["text"])
    L2.by_key[it1["key"]] = L2.T
    sg = suggest(it1, L2, 19.0, "sonnet")
    res["suggest_serves_on_agreement"] = sg.get("A2S") is not None and abs(sg["A2S"][0] - 19) < 1e-9
    res["suggest_refuses_on_disagreement"] = suggest(it1, L2, 5.0, "sonnet").get("A2S") is None
    # KC needs 3 donors
    res["KC_needs_3"] = suggest(it1, L2, None, "sonnet").get("KC") is None
    # PC control: exact path must not serve a concept MC item; a numeric MC-disguised item is graded only as escalation
    itpc = {"id": "pc", "text": "Compounds that accept electrons are called what? (A) oxidants (B) residues (C) antioxidants (D) oxygen", "gold_type": "mc", "gold": "A", "numbers": {}, "key": "other|0|"}
    v, why = exact(itpc, Lib())
    res["PC_not_served"] = v is None
    # G-P6 arm rule: haiku rule, sonnet reported
    row_bad = {"g6": False, "rule": None}
    res["G6_rule_haiku"] = not gates_pass(row_bad, "haiku")
    res["G6_reported_sonnet"] = gates_pass(row_bad, "sonnet")
    # token instrument positive control is procedural (bridge/usage.jsonl must contain the empty-batch row) -> checked in tokens()
    res["pass"] = all(v for k, v in res.items() if k != "pass")
    (OUT / "controls110.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sample", "run", "tokens", "controls"])
    ap.add_argument("--split", default="acq")
    ap.add_argument("--arm", default="det")
    ap.add_argument("--checkpoint", type=int, default=0)
    ap.add_argument("--lib-in", default=None)
    ap.add_argument("--lib-out", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tiers", default=None, help="comma list")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    if a.cmd == "sample":
        write_batches(a.split, a.tiers.split(",") if a.tiers else None)
    elif a.cmd == "run":
        run(a.arm, a.split, a.checkpoint, a.lib_in, a.lib_out, a.limit, a.tiers.split(",") if a.tiers else None, a.tag)
    elif a.cmd == "tokens":
        tokens()
    else:
        controls()


if __name__ == "__main__":
    main()
