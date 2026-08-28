"""V0.5 multi-generation breeder (Sections 22-23).

Reuses V0.4's validated machinery (trace mining + LLM proposal, both judged
by the same _q90 held-out validator) but parameterized by the CURRENT
registry so generations can stack: gen0 -> traffic -> gen1 -> traffic ->
gen2 ...

Additional V0.5 gates before a generation is deployed (Section 22), all
using train/validation data only:
  G1 wrong-fire gate   the candidate registry must produce ZERO numeric
                       answers on the validation adversarial items in PURE
                       mode; a bred cap implicated in a wrong-fire is
                       dropped from the generation.
  G2 regression gate   validation items the OLD registry answered correctly
                       in pure mode must stay correct under the NEW one.
Sealed evaluation happens elsewhere (lifetime driver), never here.
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401,E402
from v4 import registry_v4 as R4                  # noqa: E402
from v4.registry_v4 import _KV                    # noqa: E402
from v4.breeder import (breed_trace_mining, breed_llm_proposal,  # noqa
                        breed_raw_answer, _expr_from_form,
                        _expr_from_kinds)
from v4.analyze_v4 import grade                   # noqa: E402


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def observations_from_records(recs):
    obs = []
    for r in recs:
        for h in r.get("handoffs", []):
            if h.get("accepted") and h.get("state_at_handoff") \
                    and h.get("value") is not None:
                obs.append({"trace_id": r["query_id"],
                            "state": h["state_at_handoff"],
                            "target": h["target_kind"],
                            "value": float(h["value"])})
    return obs


# ---------------------------------------------------------------------------
# V0.5 robust validation (designed 2026-08-24 from MEASURED regime-C traffic
# pollution, before any sealed data was consulted): accepted-but-wrong LLM
# handoffs contaminate up to 49% of observations for a target (e.g. the
# J->kWh conversion omitted — a WRONG formula produces its own tight
# implied-coefficient cluster). V0.4's q90 validator assumes <=10% pollution
# and rejects everything at these rates. Replacement rule: the largest
# 1%-relative cluster of implied coefficients must contain >= DOM_FRAC of
# all observations AND >= MIN_SUPPORT members; the coefficient is the
# cluster median; residual is q90 WITHIN the cluster. A wrong-formula
# cluster can win only by out-numbering the true one — and the G3
# validation-accuracy deployment gate (below) kills any wrong-constant
# capability against known validation truths.
# ---------------------------------------------------------------------------
DOM_FRAC = 0.5
DOM_FRAC_RELATIVE = 0.35   # with >=2x margin over the runner-up cluster
MIN_SUPPORT = 5
RESID_TOL = 0.01


def _dominant_cluster(vals, tol=RESID_TOL):
    """(center, members, frac, second_size): largest cluster under relative
    tol, plus the size of the largest DISJOINT runner-up cluster.

    Dominance is judged against the runner-up CLUSTER, not against
    scattered noise: measured regime-C traffic showed the true J->kWh
    cluster at 49.2% of observations with the remainder scattered across
    unrelated wrong values — an absolute-majority rule rejected it while
    no competing hypothesis existed. Accept if frac >= DOM_FRAC, or
    frac >= DOM_FRAC_RELATIVE with >= 2x margin over the runner-up
    (the G3 validation-accuracy gate remains the final arbiter)."""
    if not vals:
        return None, [], 0.0, 0
    vs = sorted(vals)
    best = (None, [])
    for c in vs:
        members = [v for v in vs if abs(v - c) <= tol * max(abs(c), 1e-12)]
        if len(members) > len(best[1]):
            import statistics
            best = (statistics.median(members), members)
    rest = list(vs)
    for m in best[1]:
        rest.remove(m)
    second = (None, [])
    for c in rest:
        members = [v for v in rest
                   if abs(v - c) <= tol * max(abs(c), 1e-12)]
        if len(members) > len(second[1]):
            second = (c, members)
    return (best[0], best[1], len(best[1]) / len(vs), len(second[1]))


def _dominant_ok(frac, n_members, second_size):
    if n_members < MIN_SUPPORT:
        return False
    if frac >= DOM_FRAC:
        return True
    return frac >= DOM_FRAC_RELATIVE and n_members >= 2 * max(1,
                                                              second_size)


def _fit_form_robust(form, fn, rows):
    """rows: [(xs, y)]. Dominant-cluster fit over ALL rows' implied
    coefficients (no fit/val split — the cluster criterion subsumes it:
    every member is an independent observation the formula must hit to
    1%)."""
    implied = []
    for xs, y in rows:
        try:
            base = fn(xs, 1.0)
        except ZeroDivisionError:
            return None
        if abs(base) < 1e-12:
            return None
        implied.append(y / base)
    if "a" not in form:
        members = [i for i in implied if abs(i - 1.0) <= RESID_TOL]
        rest = [i for i in implied if abs(i - 1.0) > RESID_TOL]
        _, sec_m, _, _ = _dominant_cluster(rest) if rest else (None, [],
                                                              0.0, 0)
        frac = len(members) / len(implied)
        if not _dominant_ok(frac, len(members), len(sec_m)):
            return None
        resid = sorted(abs(i - 1.0) for i in members)[
            min(len(members) - 1, int(0.9 * (len(members) - 1)))]
        return {"a": 1.0, "residual": resid, "inlier_frac": frac,
                "inliers": len(members)}
    a, members, frac, second = _dominant_cluster(implied)
    if a is None or not _dominant_ok(frac, len(members), second):
        return None
    errs = sorted(abs(m - a) / max(abs(a), 1e-12) for m in members)
    resid = errs[min(len(errs) - 1, int(0.9 * (len(errs) - 1)))]
    if resid > RESID_TOL:
        return None
    return {"a": a, "residual": resid, "inlier_frac": frac,
            "inliers": len(members)}


def breed_trace_mining_robust(obs):
    """V0.4 search loops with the robust dominant-cluster fit."""
    from collections import defaultdict as dd
    from itertools import combinations
    from v4.breeder import _FORMS
    by_target = dd(list)
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
                fit = _fit_form_robust(form, fn,
                                       [((o["state"][k],), o["value"])
                                        for o in rows])
                if fit and (best is None
                            or fit["inlier_frac"] > best["inlier_frac"]
                            or (fit["inlier_frac"] == best["inlier_frac"]
                                and fit["residual"] < best["residual"])):
                    best = {"inputs": [k], "form": form, **fit}
        for k1, k2 in combinations(sorted(common), 2):
            for order in ((k1, k2), (k2, k1)):
                for form, nx, fn in _FORMS:
                    if nx != 2:
                        continue
                    tried += 1
                    fit = _fit_form_robust(
                        form, fn,
                        [((o["state"][order[0]], o["state"][order[1]]),
                          o["value"]) for o in rows])
                    if fit and (best is None
                                or fit["inlier_frac"]
                                > best["inlier_frac"]
                                or (fit["inlier_frac"]
                                    == best["inlier_frac"]
                                    and fit["residual"]
                                    < best["residual"])):
                        best = {"inputs": list(order), "form": form,
                                **fit}
        if best is not None:
            cands.append({"method": "trace_mining", "output": target,
                          "support": len(rows),
                          "trace_ids": [o["trace_id"] for o in rows],
                          "created_at": _now(), **best})
    return cands, {"targets": len(by_target), "fits_tried": tried,
                   "validator": "dominant_cluster"}


def breed_llm_proposal_robust(obs, generate_json=None):
    """V0.4 proposal method with (1) ^ -> ** normalization and (2) the
    dominant-cluster inlier criterion on ALL observations instead of the
    q90 fit/val split."""
    import math
    import re as _re
    from collections import defaultdict as dd
    from v4 import llm_bridge
    gj = generate_json or llm_bridge.generate_json
    by_target = dd(list)
    for o in obs:
        by_target[o["target"]].append(o)
    cands, meta = [], {"targets": 0, "proposals": 0, "llm_calls": 0,
                       "validator": "dominant_cluster"}
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
            "them. Note: a minority of observations may be corrupted — "
            "propose the formula that explains the majority.\n\n"
            + json.dumps(ex, indent=1) +
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
        expr = expr.replace("^", "**")
        if not inputs or not all(
                _re.fullmatch(r"[a-z_][a-z0-9_]*", i) for i in inputs):
            continue
        if not _re.fullmatch(r"[\w\s+\-*/().]+", expr.replace("**", "")):
            continue
        errs = []
        for o in rows:
            if not all(k in o["state"] for k in inputs):
                errs = None
                break
            try:
                pred = eval(expr, {"__builtins__": {}, "math": math},
                            {k: o["state"][k] for k in inputs})
            except Exception:
                errs = None
                break
            if not (isinstance(pred, (int, float))
                    and math.isfinite(pred)):
                errs = None
                break
            errs.append(abs(pred - o["value"])
                        / max(1e-9, abs(o["value"])))
        if errs is None:
            continue
        inliers = [e for e in errs if e <= RESID_TOL]
        frac = len(inliers) / len(errs)
        # runner-up cluster among the OUTLIER prediction ratios is not
        # well-defined for proposals (errors, not coefficients); use the
        # relative rule with second=0 only when the outliers are scattered
        # (no tight tie), which the mining side already guards — here the
        # absolute branch OR the relative branch with a conservative
        # second-size estimate applies
        rest = [e for e in errs if e > RESID_TOL]
        _, sec_m, _, _ = _dominant_cluster(rest) if rest else (None, [],
                                                               0.0, 0)
        if _dominant_ok(frac, len(inliers), len(sec_m)):
            resid = sorted(inliers)[min(len(inliers) - 1,
                                        int(0.9 * (len(inliers) - 1)))]
            cands.append({"method": "llm_proposal", "output": target,
                          "inputs": inputs, "expr_kinds": expr,
                          "support": len(rows), "residual": resid,
                          "inlier_frac": frac, "inliers": len(inliers),
                          "trace_ids": [o["trace_id"] for o in rows],
                          "created_at": _now()})
    return cands, meta


def _collides_in(reg, inputs, output):
    for name, spec in reg.items():
        if spec.get("transfer"):
            continue
        if spec["output"] == output and set(spec["inputs"]) == set(inputs):
            return name
    return None


def build_generation(current_reg, mined, proposed, gen_idx):
    accepted, provenance = {}, []
    for c in mined + proposed:
        key = (tuple(sorted(c["inputs"])), c["output"])
        col = _collides_in(current_reg, c["inputs"], c["output"])
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
        while name in current_reg or name in accepted or \
                any(v["name"] == name for v in accepted.values()):
            i += 1
            name = f"bred_{c['output']}_{i}"
        accepted[key] = {"name": name,
                         "spec": {"inputs": list(c["inputs"]),
                                  "output": c["output"],
                                  "equation": f"bred: {c['method']} "
                                              f"gen{gen_idx}",
                                  "expr": expr, "domain": "bred"}}
        provenance.append({**c, "accepted": True, "cap_name": name,
                           "expr": expr, "generation": gen_idx})
    reg_new = dict(current_reg)
    for v in accepted.values():
        reg_new[v["name"]] = v["spec"]
    return reg_new, provenance


def _val_items():
    return json.loads((ROOT / "data" / "v0.4_validation.json").read_text(
        encoding="utf-8"))


def safety_gate(reg_new, current_reg, gen_idx):
    """G1+G2 on validation only. Returns (final_reg, gate_report)."""
    from v5.engine5 import V5Engine
    val = _val_items()
    new_caps = sorted(set(reg_new) - set(current_reg))
    report = {"generation": gen_idx, "new_caps": new_caps,
              "wrong_fires": [], "regressions": [], "dropped": []}
    if not new_caps:
        return reg_new, report
    eng_new = V5Engine(mode="partial", integrity=True, depaware=True,
                       registry=reg_new)
    eng_old = V5Engine(mode="partial", integrity=True, depaware=True,
                       registry=current_reg)
    dropped = set()
    for it in val:
        if not (it.get("unanswerable") or it["domains"] == ["ood"]):
            continue
        r = eng_new.process(it["query"], mode_llm="pure")
        if r.get("numeric_value") is not None:
            culprits = [c for c in new_caps if c in (r.get("path") or [])]
            report["wrong_fires"].append(
                {"item": it["id"], "path": r.get("path"),
                 "culprits": culprits})
            dropped.update(culprits or new_caps)
    for it in val:
        if it.get("unanswerable") or it["domains"] == ["ood"]:
            continue
        r_new = eng_new.process(it["query"], mode_llm="pure")
        ok_new, _ = grade(it, r_new)
        used_bred = [c for c in new_caps if c in (r_new.get("path") or [])]
        if ok_new:
            continue
        # G3 validation-accuracy gate: a validation item answered WRONGLY
        # through a bred capability kills that capability. This is what
        # catches a wrong-constant formula whose polluted observation
        # cluster out-voted the true one — validation truths are the
        # arbiter, and validation is fair game.
        if used_bred:
            report["regressions"].append(
                {"item": it["id"], "culprits": used_bred, "gate": "G3"})
            dropped.update(used_bred)
            continue
        # G2 regression gate: previously-correct pure answers must stay
        # correct under the new registry
        r_old = eng_old.process(it["query"], mode_llm="pure")
        ok_old, _ = grade(it, r_old)
        if ok_old:
            report["regressions"].append(
                {"item": it["id"], "culprits": [], "gate": "G2"})
            dropped.update(new_caps)
    if dropped:
        report["dropped"] = sorted(dropped)
        reg_final = {k: v for k, v in reg_new.items() if k not in dropped}
        return reg_final, report
    return reg_new, report


def breed_generation(recs, traffic_items, current_reg, gen_idx,
                     consumed_trace_ids=frozenset()):
    """One breeder generation from accumulated stream records. Observations
    already consumed by earlier generations are excluded from support
    counting? NO — support counts ALL observations (a capability's evidence
    doesn't expire); dedup happens at the (inputs, output) collision level.
    Returns (final_reg, {stats})."""
    obs = observations_from_records(recs)
    mined, mine_meta = breed_trace_mining_robust(obs)
    # LLM proposals cost a real call per target: skip targets this registry
    # already produces via a bred capability (their proposals would only be
    # collision-rejected), and targets mining just solved this generation
    # (mining wins ties anyway). Mining stays unfiltered (free).
    bred_outputs = {spec["output"] for name, spec in current_reg.items()
                    if name.startswith("bred_")}
    bred_outputs |= {c["output"] for c in mined}
    obs_new = [o for o in obs if o["target"] not in bred_outputs]
    proposed, prop_meta = breed_llm_proposal_robust(obs_new)
    raw_c, raw_meta = breed_raw_answer(
        traffic_items, [r for r in recs
                        if r.get("numeric_value") is not None])
    reg_new, provenance = build_generation(current_reg, mined, proposed,
                                           gen_idx)
    reg_final, gate = safety_gate(reg_new, current_reg, gen_idx)
    stats = {"generation": gen_idx, "observations": len(obs),
             "mined": len(mined), "proposed": len(proposed),
             "raw_answer_candidates": len(raw_c),
             "raw_answer_note": "measured but NEVER deployed (V0.4 showed "
                                "memorization is the failure baseline)",
             "provenance": provenance, "gate": gate,
             "mine_meta": mine_meta, "prop_meta": prop_meta,
             "new_caps_deployed": sorted(set(reg_final)
                                         - set(current_reg)),
             "registry_hash": R4.registry_hash(reg_final),
             "created_at": _now()}
    return reg_final, stats
