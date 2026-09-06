# -*- coding: utf-8 -*-
# origin: new for V1.8 -- plan-to-template harvest (SPEC 4.2)
"""Certified plan -> role-slot template -> two-donor rule -> probation
on ACQ -> library. Only the model's own input (the question text) and
output (its plan) are used; the dataset's reference plan is never
read (planlib17's honesty rule, kept).

  python tools/harvest18.py build   --model <m> --scope dev|all
  python tools/harvest18.py probate --model <m> --scope dev|all
  python tools/harvest18.py union   --scope dev|all

scope dev  = the model's DEV-phase admitted plans only (the apples-to-
             apples library against V1.7's stack_<m>, which replayed
             dev-phase templates)
scope all  = dev + sealed-phase plans; a template never serves its own
             donor question (binder18 exclude_donors)

build:   results/v18/harvest_<m>_<scope>.json
probate: results/v18/planlib18_<m>_<scope>.json + harvest ledger
union:   results/v18/planlib18_all_<scope>.json
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))
from reflex import roles18 as R  # noqa: E402

DATA = HERE / "results" / "v17" / "data"
V17 = HERE / "results" / "v17"
OUT = HERE / "results" / "v18"
MODELS = ["haiku", "sonnet", "opus", "fable"]
_WS = re.compile(r"\s+")


def _load_items(splits):
    out = {}
    for s in splits:
        with open(DATA / ("q1m_%s.jsonl" % s), encoding="utf-8") as f:
            for line in f:
                it = json.loads(line)
                out[it["id"]] = it
    return out


def _certified(model, phase):
    """(id, plan) pairs the witness certified CORRECT against gold."""
    scored = json.loads((V17 / ("plans_%s_%s.json" % (model, phase)))
                        .read_text(encoding="utf-8"))
    good = {r["id"] for r in scored["rows"]
            if r.get("gate") and r.get("correct") is True}
    lib = json.loads((V17 / ("planlib_%s_%s.json" % (model, phase)))
                     .read_text(encoding="utf-8"))
    return [(a["id"], a["plan"]) for a in lib if a["id"] in good]


def _norm_plan(plan):
    """Canonical form for grouping AND serving: ids renumbered in
    order, expression whitespace removed (not semantic), numerics as
    floats, and a formula node's unit set to its CERTIFIED unit (the
    kind is fixed by G-P5's table, so the annotation is derivable; a
    model unit that disagrees with the certified one is a rejected
    plan -> returns None)."""
    from reflex.plangate18 import CERTIFIED_FORMULAS, _equiv
    idmap = {n["id"]: "n%d" % (i + 1) for i, n in
             enumerate(plan["nodes"])}

    def fix(v):
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            s = v
            for old, new in idmap.items():
                s = re.sub(r"@%s\b" % re.escape(old), "@" + new, s)
            return _WS.sub("", s) if ("@" in s or any(
                c in s for c in "*+-/^(")) else s.strip()
        return v
    nodes = []
    for n in plan["nodes"]:
        nd = {}
        for k in sorted(n):
            nd[k] = idmap[n[k]] if k == "id" else fix(n[k])
        if nd.get("op") == "formula":
            cu = None
            for _kind, (canon, unit) in CERTIFIED_FORMULAS.items():
                if _equiv(n.get("expr") or "", canon):
                    cu = unit
                    break
            if cu is None:
                return None
            if nd.get("unit") not in (None, cu):
                return None
            nd["unit"] = cu
        nodes.append(nd)
    return {"nodes": nodes, "final": idmap[plan["final"]]}


def templateize(text, plan):
    """-> (template dict, None) or (None, reason)."""
    roles = R.analyze(text)
    if roles.bare():
        return None, "unresolved_donor"
    uniq = roles.unique
    consumed = set()
    nodes_t, node_steps = [], []

    def take(pred):
        for i, t in enumerate(uniq):
            if i not in consumed and pred(t):
                consumed.add(i)
                return t
        return None

    for n in plan["nodes"]:
        op = n.get("op")
        nd = {}
        steps_used = set()
        for k, v in n.items():
            if k in R.NON_SLOT_KEYS and k != "rhs":
                nd[k] = v
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                nd[k] = v
                continue
            role = R.slot_role(op, k)
            if role == "STRUCTURAL":
                nd[k] = v
                continue
            if role is None:
                return None, "unrolled:%s.%s" % (op, k)
            mag = abs(float(v))
            t = take(lambda t: t.cue == role and abs(t.value - mag) < 1e-9)
            if t is None:
                return None, "literal_no_token:%s.%s" % (op, k)
            nd[k] = "$s%d|%s|%d" % (t.step, t.cue, t.ord)
            steps_used.add(t.step)
        if op in R.EXPR_OPS:
            for k in R.EXPR_KEYS:
                v = n.get(k)
                if not isinstance(v, str):
                    continue
                s, last = "", 0
                for st, en, mag in R.expr_numbers(v):
                    fm = float(mag)
                    t = take(lambda t: t.cue in R.EXPR_TOKEN_CUES and
                             abs(t.value - fm) < 1e-9)
                    if t is None:
                        return None, "expr_no_token:%s" % op
                    s += v[last:st] + "{$s%d|%s|%d}" % (t.step, t.cue,
                                                        t.ord)
                    last = en
                    steps_used.add(t.step)
                nd[k] = s + v[last:]
            if op == "solve_pick" and "rhs" not in n:
                t = take(lambda t: t.cue == "rhs" and t.value == 0.0)
                if t is not None:
                    steps_used.add(t.step)
        nodes_t.append(nd)
        node_steps.append(sorted(steps_used))
    if len(consumed) != len(uniq):
        return None, "token_unconsumed"
    return {"skeleton": roles.skeleton, "n_steps": len(roles.steps),
            "plan": {"nodes": nodes_t, "final": plan["final"]},
            "node_steps": node_steps,
            "step_skeletons": [R.skeleton_of(s) for s in roles.steps],
            "ends_q": text.rstrip().endswith("?")}, None


_SMARK = re.compile(r"\$s(\d+)\|")


def _shift(v, delta, idmap):
    if not isinstance(v, str):
        return v
    s = _SMARK.sub(lambda m: "$s%d|" % (int(m.group(1)) + delta), v)
    for old, new in idmap.items():
        s = re.sub(r"@%s\b" % re.escape(old), "@" + new, s)
    return s


def subchains(tpl):
    """Contiguous sub-plans k=2..m-1 of an aligned template (one node
    per clause, each node's tokens from its own clause)."""
    nodes = tpl["plan"]["nodes"]
    m = tpl["n_steps"]
    if len(nodes) != m or m < 3:
        return []
    for i, st in enumerate(tpl["node_steps"]):
        if any(s != i for s in st):
            return []
    out = []
    for i in range(m):
        for j in range(i + 1, m):
            L = j - i + 1
            if L < 2 or L > m - 1:
                continue
            win = nodes[i:j + 1]
            ids = {n["id"] for n in win}
            refs_ok = True
            for wi, n in enumerate(win):
                for k, v in n.items():
                    if k == "id" or not isinstance(v, str):
                        continue
                    for r in re.findall(r"@(n\d+)\b", v):
                        if r not in ids or wi == 0:
                            refs_ok = False
            if not refs_ok:
                continue
            idmap = {n["id"]: "n%d" % (wi + 1) for wi, n in enumerate(win)}
            new_nodes = []
            for n in win:
                nd = {k: (idmap[v] if k == "id" else _shift(v, -i, idmap))
                      for k, v in n.items()}
                new_nodes.append(nd)
            skel = ". ".join(tpl["step_skeletons"][i:j + 1])
            skel += "?" if (j == m - 1 and tpl["ends_q"]) else "."
            out.append({"skeleton": skel, "n_steps": L,
                        "plan": {"nodes": new_nodes,
                                 "final": idmap[win[-1]["id"]]},
                        "window": [i, j]})
    return out


def build(model, scope):
    phases = ["dev"] if scope == "dev" else ["dev", "sealed"]
    items = _load_items(["dev", "seal"])
    led = Counter()
    # two-donor rule (SPEC 4.2): group by the role-tagged PLAN (=
    # structure signature + role assignment); each group serves the
    # exact skeletons of its donors -- every phrasing served was a
    # certified donor's phrasing, and the plan+roles are identical
    groups = defaultdict(lambda: {"donors": set(), "kind": None,
                                  "plan": None, "skeletons": set(),
                                  "n_steps": None, "parent_k": set()})

    def add(key, plan_n, skel, kind, n_steps, qid, k):
        g = groups[key]
        g["donors"].add(qid)
        g["kind"] = g["kind"] if g["kind"] == "full" else kind
        g["plan"] = plan_n
        g["skeletons"].add(skel)
        g["n_steps"] = n_steps
        g["parent_k"].add(k)

    for ph in phases:
        for qid, plan in _certified(model, ph):
            led["plans_in"] += 1
            it = items.get(qid)
            if it is None:
                led["item_missing"] += 1
                continue
            tpl, why = templateize(it["text"], plan)
            if tpl is None:
                led["reject_" + why.split(":")[0]] += 1
                continue
            pn = _norm_plan(tpl["plan"])
            if pn is None:
                led["reject_formula_unit"] += 1
                continue
            led["templated_full"] += 1
            add(json.dumps(pn, sort_keys=True), pn, tpl["skeleton"],
                "full", tpl["n_steps"], qid, len(plan["nodes"]))
            for sub in subchains(tpl):
                pn2 = _norm_plan(sub["plan"])
                if pn2 is None:
                    continue
                led["templated_sub"] += 1
                add(json.dumps(pn2, sort_keys=True), pn2, sub["skeleton"],
                    "sub", sub["n_steps"], qid, len(plan["nodes"]))
    cands, single = [], []
    skel_plans = defaultdict(set)
    for pj, g in groups.items():
        for sk in g["skeletons"]:
            skel_plans[sk].add(pj)
        entry = {"skeletons": sorted(g["skeletons"]), "plan": g["plan"],
                 "kind": g["kind"], "n_steps": g["n_steps"],
                 "donors": sorted(g["donors"]),
                 "parent_k": sorted(g["parent_k"]), "models": [model]}
        if len(g["donors"]) >= 2:
            cands.append(entry)
            led["two_donor_" + g["kind"]] += 1
        else:
            single.append(entry)
            led["single_donor_" + g["kind"]] += 1
    led["skeletons"] = len(skel_plans)
    led["skeleton_collisions"] = sum(
        1 for v in skel_plans.values() if len(v) > 1)
    cands.sort(key=lambda e: (e["kind"], e["skeletons"][0]))
    for i, e in enumerate(cands):
        e["name"] = "%s_%s_%04d" % (model, e["kind"], i)
    out = {"model": model, "scope": scope, "ledger": dict(led),
           "candidates": cands, "single_donor": single}
    p = OUT / ("harvest_%s_%s.json" % (model, scope))
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({"model": model, "scope": scope,
                      "ledger": dict(led)}, indent=1))


def probate(model, scope, cap=100):
    import v17_run as RUN
    from reflex import binder18
    h = json.loads((OUT / ("harvest_%s_%s.json" % (model, scope)))
                   .read_text(encoding="utf-8"))
    cands = h["candidates"]
    acq = _load_items(["acq"])
    by_skel = defaultdict(list)
    for it in acq.values():
        if it.get("distractor"):
            continue
        by_skel[R.skeleton_of(it["text"])].append(it)
    led = Counter()
    admitted, kills = [], []
    for c in cands:
        lib = binder18.Library([c])
        serves, tuples, dead = [], set(), None
        pool = []
        for sk in c["skeletons"]:
            pool.extend(by_skel.get(sk, []))
        # probation cap: a popular sub-chain skeleton matches thousands
        # of ACQ items; probation needs >=3 clean serves on >=3 tuples,
        # the full DEV-L/SEAL runs exercise every template at volume
        pool = pool[:cap]
        for it in pool:
            v, cert, info = binder18.serve(it["text"], lib, qid=it["id"])
            if v is None:
                led["probe_abstain_" + (info["reason"] or "?").split(
                    ":")[0]] += 1
                continue
            g = (v > 0) if it.get("gold_type") == "bool" else v
            good = RUN.grade(it, g)
            serves.append(it["id"])
            tuples.add(tuple(str(x) for x in re.findall(
                r"-?\d+(?:\.\d+)?", it["text"])))
            if not good:
                dead = "g3: WRONG bound serve on %s" % it["id"]
                break
        if dead:
            led["g3_wrong"] += 1
            kills.append({"name": c["name"], "why": dead})
        elif len(serves) < 3:
            led["g3_inert"] += 1
            kills.append({"name": c["name"],
                          "why": "g3: inert (%d)" % len(serves)})
        elif len(tuples) < 3:
            led["g3_memorize"] += 1
            kills.append({"name": c["name"], "why": "g3: <3 tuples"})
        else:
            e = dict(c)
            e["probation"] = {"serves": len(serves),
                              "tuples": len(tuples)}
            admitted.append(e)
            led["admitted"] += 1
            led["admitted_" + c["kind"]] += 1
    led["candidates"] = len(cands)
    out = {"model": model, "scope": scope, "ledger": dict(led),
           "harvest_ledger": h["ledger"], "kills": kills,
           "templates": admitted}
    (OUT / ("planlib18_%s_%s.json" % (model, scope))).write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({"model": model, "scope": scope,
                      "ledger": dict(led)}, indent=1))


def union(scope):
    groups = {}
    led = Counter()
    for m in MODELS:
        p = OUT / ("planlib18_%s_%s.json" % (m, scope))
        if not p.exists():
            continue
        for t in json.loads(p.read_text(encoding="utf-8"))["templates"]:
            key = json.dumps(t["plan"], sort_keys=True)
            if key in groups:
                g = groups[key]
                g["donors"] = sorted(set(g["donors"]) | set(t["donors"]))
                g["models"] = sorted(set(g["models"]) | set(t["models"]))
                g["skeletons"] = sorted(set(g["skeletons"]) |
                                        set(t["skeletons"]))
                led["merged"] += 1
            else:
                groups[key] = dict(t)
                led["templates"] += 1
    skels = Counter(sk for g in groups.values() for sk in g["skeletons"])
    led["skeleton_collisions"] = sum(1 for v in skels.values() if v > 1)
    tpls = list(groups.values())
    for i, t in enumerate(tpls):
        t["name"] = "all_%s_%04d" % (t["kind"], i)
    (OUT / ("planlib18_all_%s.json" % scope)).write_text(
        json.dumps({"model": "all", "scope": scope, "ledger": dict(led),
                    "templates": tpls}, indent=1), encoding="utf-8")
    print(json.dumps({"scope": scope, "ledger": dict(led)}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "probate", "union"])
    ap.add_argument("--model", default=None, choices=MODELS)
    ap.add_argument("--scope", default="dev", choices=["dev", "all"])
    ap.add_argument("--cap", type=int, default=100)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.cmd == "build":
        build(a.model, a.scope)
    elif a.cmd == "probate":
        probate(a.model, a.scope, a.cap)
    else:
        union(a.scope)


if __name__ == "__main__":
    main()
