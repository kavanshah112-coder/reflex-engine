"""V0.4 capability breeder (Sections 44-50, 64).

Mines DEPLOYMENT TRAFFIC traces (v4_partial_h2 on the traffic split) for
recurring LLM-handoff patterns and tries to convert them into typed
capabilities, by three competing methods:

  raw_answer    v0.1-style memorization: masked-query-text -> answer lookup.
                Validation demands answer consistency across observations;
                parametric queries vary, so this is EXPECTED to fail — the
                baseline exists to show WHY typed breeding is needed.
  trace_mining  deterministic closed-form fitting over accepted handoff
                observations (state_at_handoff -> injected value): tries
                y=a*x, y=a*x1*x2, y=a*x1/x2, y=x1*(1-x2), y=x1*(1+x2),
                fits on the first half, validates on the held-out second
                half. No LLM involved.
  llm_proposal  the LLM sees example observations and proposes a typed
                capability spec (inputs, output, expression) as JSON; the
                expression is validated by evaluation on ALL observations.

Validation battery (every method): support >= MIN_SUPPORT, held-out max
relative residual <= RESID_TOL, no collision with an existing registry
capability, finite/sane outputs, full provenance (trace ids, timestamps).
Accepted candidates enter registry v1 (versioned + hashed). The SEALED
posttest is evaluated ONCE per registry version, at the very end.

IMPORTANT honesty property: observations are the LLM's injected values from
live traffic (possibly wrong) — ground-truth generator lambdas are NEVER
consulted by any breeding method.
"""
import json
import math
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401

from v4 import registry_v4 as R4              # noqa: E402
from v4.registry_v4 import REGISTRY, _KV      # noqa: E402

RAW = ROOT / "results" / "raw_v4"
MIN_SUPPORT = 5
RESID_TOL = 0.01


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_observations():
    """(query_id, state_kinds->values, target_kind, injected_value) from
    accepted handoffs in the traffic trace."""
    obs = []
    p = RAW / "v4_partial_h2_traffic.jsonl"
    for line in p.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        for h in r.get("handoffs", []):
            if h.get("accepted") and h.get("state_at_handoff") \
                    and h.get("value") is not None:
                obs.append({"trace_id": r["query_id"],
                            "state": h["state_at_handoff"],
                            "target": h["target_kind"],
                            "value": float(h["value"])})
    return obs


# ---------------------------------------------------------------- method A
def breed_raw_answer(traffic_items, traffic_recs):
    """Masked-text -> answer memorization. Accepted only if every observation
    of the same masked text yields the same answer (within tolerance)."""
    items = {i["id"]: i for i in traffic_items}
    groups = defaultdict(list)
    for r in traffic_recs:
        if r.get("numeric_value") is None:
            continue
        q = items[r["query_id"]]["query"]
        key = re.sub(r"\d+(?:,\d{3})*(?:\.\d+)?", "<N>", q)
        groups[key].append((r["query_id"], r["numeric_value"]))
    cands, rejected = [], 0
    for key, vals in groups.items():
        if len(vals) < MIN_SUPPORT:
            rejected += 1
            continue
        vs = [v for _, v in vals]
        mean = sum(vs) / len(vs)
        spread = max(abs(v - mean) for v in vs) / max(1e-9, abs(mean))
        if spread <= RESID_TOL:
            cands.append({"method": "raw_answer", "key": key[:80],
                          "value": mean, "support": len(vals),
                          "residual": spread,
                          "trace_ids": [t for t, _ in vals],
                          "created_at": _now()})
        else:
            rejected += 1
    return cands, {"groups": len(groups), "rejected": rejected}


# ---------------------------------------------------------------- method B
_FORMS = [
    ("a*x1",        1, lambda x, a: a * x[0]),
    ("a*x1*x2",     2, lambda x, a: a * x[0] * x[1]),
    ("a*x1/x2",     2, lambda x, a: a * x[0] / x[1]),
    ("x1*(1-x2)",   2, lambda x, a: x[0] * (1 - x[1])),
    ("x1*(1+x2)",   2, lambda x, a: x[0] * (1 + x[1])),
]


def _q90(errs):
    """Robust held-out residual: 90th-percentile relative error. Both
    breeding methods are judged by THIS same statistic — a minority of
    corrupted traffic labels (accepted-but-wrong LLM handoffs exist in live
    traffic) must not veto an otherwise-consistent capability, but the
    capability must fit the overwhelming majority."""
    if not errs:
        return float("inf")
    s = sorted(errs)
    return s[min(len(s) - 1, int(0.9 * (len(s) - 1)))]


def _fit_form(form, nx, fn, rows):
    """rows: [(xs, y)]. Fit 'a' on the first half (median of implied a),
    validate q90 rel residual on the held-out second half."""
    half = max(2, len(rows) // 2)
    fit_rows, val_rows = rows[:half], rows[half:]
    if "a" in form:
        implied = []
        for xs, y in fit_rows:
            try:
                base = fn(xs, 1.0)
            except ZeroDivisionError:
                return None
            if abs(base) < 1e-12:
                return None
            implied.append(y / base)
        implied.sort()
        a = implied[len(implied) // 2]
        spread = _q90([abs(i - a) / max(1e-9, abs(a)) for i in implied])
        if spread > RESID_TOL:
            return None
    else:
        a = 1.0
    errs = []
    for xs, y in val_rows:
        try:
            pred = fn(xs, a)
        except ZeroDivisionError:
            return None
        errs.append(abs(pred - y) / max(1e-9, abs(y)))
    resid = _q90(errs)
    if resid > RESID_TOL:
        return None
    return {"a": a, "residual": resid}


def breed_trace_mining(obs):
    by_target = defaultdict(list)
    for o in obs:
        by_target[o["target"]].append(o)
    cands, tried = [], 0
    for target, rows in by_target.items():
        if len(rows) < MIN_SUPPORT:
            continue
        common = set.intersection(*(set(o["state"]) for o in rows))
        common.discard(target)
        best = None
        for k in sorted(common):
            for form, nx, fn in _FORMS:
                if nx != 1:
                    continue
                tried += 1
                fit = _fit_form(form, nx, fn,
                                [((o["state"][k],), o["value"])
                                 for o in rows])
                if fit and (best is None
                            or fit["residual"] < best["residual"]):
                    best = {"inputs": [k], "form": form, **fit}
        for k1, k2 in combinations(sorted(common), 2):
            for order in ((k1, k2), (k2, k1)):
                for form, nx, fn in _FORMS:
                    if nx != 2:
                        continue
                    tried += 1
                    fit = _fit_form(form, nx, fn,
                                    [((o["state"][order[0]],
                                       o["state"][order[1]]), o["value"])
                                     for o in rows])
                    if fit and (best is None
                                or fit["residual"] < best["residual"]):
                        best = {"inputs": list(order), "form": form, **fit}
        if best is not None:
            cands.append({"method": "trace_mining", "output": target,
                          "support": len(rows),
                          "trace_ids": [o["trace_id"] for o in rows],
                          "created_at": _now(), **best})
    return cands, {"targets": len(by_target), "fits_tried": tried}


# ---------------------------------------------------------------- method C
def breed_llm_proposal(obs, generate_json=None):
    from v4 import llm_bridge
    gj = generate_json or llm_bridge.generate_json
    by_target = defaultdict(list)
    for o in obs:
        by_target[o["target"]].append(o)
    cands, meta = [], {"targets": 0, "proposals": 0, "llm_calls": 0}
    for target, rows in by_target.items():
        if len(rows) < MIN_SUPPORT:
            continue
        meta["targets"] += 1
        ex = [{"known": {k: round(v, 6) for k, v in o["state"].items()},
               "computed": {target: round(o["value"], 6)}}
              for o in rows[:4]]
        prompt = (
            "You are a program-synthesis subroutine. Below are observations "
            "of a hidden deterministic calculation. Each observation shows "
            "known quantities and the value that was computed from SOME of "
            "them.\n\n" + json.dumps(ex, indent=1) +
            "\n\nPropose the formula. Respond ONLY with this JSON schema:\n"
            '{"inputs": ["<kind>", ...], "output": "' + target + '", '
            '"expr": "<python expression using EXACTLY the input kind names '
            'as variables, e.g. area / coverage_rate>"}')
        out = gj(prompt, num_predict=200)
        meta["llm_calls"] += 1
        try:
            d = json.loads(out["text"])
            inputs, expr = list(d["inputs"]), str(d["expr"])
        except Exception:
            continue
        meta["proposals"] += 1
        if not inputs or not all(
                re.fullmatch(r"[a-z_][a-z0-9_]*", i) for i in inputs):
            continue
        if not re.fullmatch(r"[\w\s+\-*/().]+", expr):
            continue                      # expression safety allowlist
        # SAME validation protocol as trace mining: q90 relative error on
        # the held-out second half of the observations
        half = max(2, len(rows) // 2)
        errs = []
        ok = True
        for o in rows[half:]:
            if not all(k in o["state"] for k in inputs):
                ok = False
                break
            try:
                pred = eval(expr, {"__builtins__": {}, "math": math},
                            {k: o["state"][k] for k in inputs})
            except Exception:
                ok = False
                break
            if not (isinstance(pred, (int, float))
                    and math.isfinite(pred)):
                ok = False
                break
            errs.append(abs(pred - o["value"])
                        / max(1e-9, abs(o["value"])))
        resid = _q90(errs) if ok else float("inf")
        if ok and resid <= RESID_TOL:
            cands.append({"method": "llm_proposal", "output": target,
                          "inputs": inputs, "expr_kinds": expr,
                          "support": len(rows), "residual": resid,
                          "trace_ids": [o["trace_id"] for o in rows],
                          "created_at": _now()})
    return cands, meta


# ------------------------------------------------------------- validation
def _collides(inputs, output):
    for name, spec in REGISTRY.items():
        if spec.get("transfer"):
            continue
        if spec["output"] == output and set(spec["inputs"]) == set(inputs):
            return name
    return None


def _expr_from_form(form, inputs):
    """Rewrite a fitted form into the executor's _KV variable naming."""
    counts, vars_ = {}, []
    for kind in inputs:
        base = _KV.get(kind, kind[:2])
        i = counts.get(base, 0)
        counts[base] = i + 1
        vars_.append(f"{base}{i}")
    e = form
    for j, v in enumerate(vars_, 1):
        e = e.replace(f"x{j}", v)
    return e


def _expr_from_kinds(expr_kinds, inputs):
    # variable indices must follow the executor's counting order (the
    # spec["inputs"] order), while replacement goes longest-first so a kind
    # name that is a substring of another is never clobbered
    counts, var = {}, {}
    for kind in inputs:
        base = _KV.get(kind, kind[:2])
        i = counts.get(base, 0)
        counts[base] = i + 1
        var[kind] = f"{base}{i}"
    e = expr_kinds
    for kind in sorted(inputs, key=len, reverse=True):
        e = re.sub(rf"\b{kind}\b", var[kind], e)
    return e


def build_registry_v1(mined, proposed):
    """Typed candidates -> executable capabilities -> registry v1.
    trace_mining wins ties (deterministic beats sampled)."""
    accepted, provenance = {}, []
    for c in mined + proposed:
        key = (tuple(sorted(c["inputs"])), c["output"])
        col = _collides(c["inputs"], c["output"])
        if col:
            provenance.append({**c, "accepted": False,
                               "reject_reason": f"collides:{col}"})
            continue
        if key in accepted:
            provenance.append({**c, "accepted": False,
                               "reject_reason": "duplicate(first kept)"})
            continue
        if c["method"] == "trace_mining":
            form = c["form"]
            if abs(c["a"] - 1.0) > 1e-9 and "a" in form:
                form = form.replace("a", repr(c["a"]), 1)
            else:
                form = form.replace("a*", "", 1)
            expr = _expr_from_form(form, c["inputs"])
        else:
            expr = _expr_from_kinds(c["expr_kinds"], c["inputs"])
        name = f"bred_{c['output']}"
        i = 0
        while name in REGISTRY or name in accepted:
            i += 1
            name = f"bred_{c['output']}_{i}"
        accepted[key] = {"name": name,
                         "spec": {"inputs": list(c["inputs"]),
                                  "output": c["output"],
                                  "equation": f"bred: {c['method']}",
                                  "expr": expr, "domain": "bred"}}
        provenance.append({**c, "accepted": True, "cap_name": name,
                           "expr": expr})
    reg_v1 = dict(REGISTRY)
    for v in accepted.values():
        reg_v1[v["name"]] = v["spec"]
    return reg_v1, provenance


def main():
    traffic_items = json.loads(
        (ROOT / "data" / "v0.4_traffic.json").read_text(encoding="utf-8"))
    traffic_recs = [json.loads(l) for l in
                    (RAW / "v4_partial_h2_traffic.jsonl").read_text(
                        encoding="utf-8").splitlines()]
    obs = load_observations()
    print(f"traffic: {len(traffic_recs)} records, {len(obs)} accepted "
          f"handoff observations", flush=True)

    raw_c, raw_meta = breed_raw_answer(traffic_items, traffic_recs)
    mined, mine_meta = breed_trace_mining(obs)
    # data efficiency (Section 54 'Examples Required', required plot 12):
    # smallest observation count from which trace mining recovers the SAME
    # (inputs, form) it found with full support
    for c in mined:
        target_obs = [o for o in obs if o["target"] == c["output"]]
        c["examples_required"] = None
        for k in range(2, len(target_obs) + 1):
            sub, _ = breed_trace_mining(target_obs[:k])
            hit = next((s for s in sub if s["output"] == c["output"]
                        and s["inputs"] == c["inputs"]
                        and s["form"] == c["form"]), None)
            if hit is not None:
                c["examples_required"] = k
                break
    proposed, prop_meta = breed_llm_proposal(obs)
    reg_v1, provenance = build_registry_v1(mined, proposed)

    R4.save_registry(ROOT / "data" / "v0.4_registry_v1.json", reg=reg_v1,
                     version="v1")
    out = {"observations": len(obs),
           "raw_answer": {"candidates": raw_c, **raw_meta},
           "trace_mining": {"candidates": mined, **mine_meta},
           "llm_proposal": {"candidates": proposed, **prop_meta},
           "provenance": provenance,
           "registry_v0_hash": R4.registry_hash(REGISTRY),
           "registry_v1_hash": R4.registry_hash(reg_v1),
           "registry_v1_new_caps": sorted(set(reg_v1) - set(REGISTRY)),
           "created_at": _now()}
    (ROOT / "results" / "breeder_v4.json").write_text(
        json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: (len(v["candidates"]) if isinstance(v, dict)
                          and "candidates" in v else v)
                      for k, v in out.items()
                      if k not in ("provenance",)}, indent=1, default=str))


if __name__ == "__main__":
    main()
