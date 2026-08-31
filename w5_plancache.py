# -*- coding: utf-8 -*-
# origin: new for V1.3 -- W5 plan reflexes (V1_3_SPEC section 8)
"""Serve traffic from VERIFIED plans instead of re-parsing it.

  python w5_plancache.py --mode repeat
  python w5_plancache.py --mode unique

Costs no new model calls. The cache learns only from parses this arc
already produced and verified in W2-W4, and is then replayed against
the traffic stream in order. A cache hit is bound POSITIONALLY (the
new query's numbers fill the stored schema's slots in order of
appearance) and then re-checked by the same engine that checks a
fresh parse -- round-trip, consumption, scope, dimensional,
non-degeneracy -- so a bound plan is a candidate, never an answer.

What this measures is the claim in section 8: that repeated STRUCTURE
(W0's 83.3%) can be converted into repeated SERVICE at zero parse
cost, without the confident nonsense that positional binding invites
(V0.1's founding failure).

AMENDED MID-RUN, with the reason recorded rather than the design
quietly rewritten. The first build had the cache learn only from
traffic items it had already seen solved. That can never fire here:
the arm sample is HELD OUT of the traffic pool by construction (0 of
300 arm ids appear in the 1,180-item pool), so no traffic query ever
had a verified plan waiting for it, and the run reported 3,000
escalations and nothing else.

The disjointness turns out to be the more interesting experiment. The
cache is now PRELOADED with every plan the arms verified, and replayed
against traffic those plans have never seen. The question stops being
"can a solve be reused on itself" -- which is a cache-hit tautology --
and becomes TRANSFER: does a plan verified on problem A correctly
serve problem B? That is the question the economics actually rest on,
because a cache that only helps on exact repeats is a lookup table.

One asymmetry is deliberate and reported rather than hidden: a
cache-served item has no second parse, so the AGREEMENT check -- the
pipeline's strongest discriminator on real language (D7) -- cannot
run on it. Whether the remaining deterministic checks are sufficient
without it is exactly what the wrong-fire column answers.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
DATA = HERE / "results" / "v13" / "data"
W2 = HERE / "results" / "v13" / "w2"
OUT = HERE / "results" / "v13" / "w5"


def grade(v, a, tol=2e-2):
    if v is None or a is None:
        return False
    try:
        v, a = float(v), float(a)
    except (TypeError, ValueError):
        return False
    return abs(v) < 1e-9 if a == 0 else abs(v - a) / abs(a) <= tol


ARM_SUFFIX = "_arm_sample.jsonl"      # B6: arms only, never smokes


def query_text():
    """src_id -> question text, needed to build a text-retrievable
    schema (the arm rows store the plan, not the prose)."""
    out = {}
    for f in (DATA / "v13_arm_sample.json",
              DATA / "v13_traffic_pool.json"):
        if f.exists():
            for x in json.loads(f.read_text(encoding="utf-8")):
                out[str(x["id"])] = x["q"]
    return out


def solved_corpus():
    """Every VERIFIED (query, plan) this arc has produced, from every
    ARM that has run.

    Restricted to `*_arm_sample.jsonl` (B6). Smoke and diagnostic
    files are excluded because they were produced by earlier, weaker
    check sets and are not evaluation output. Note what is NOT
    filtered: rows the arm later graded WRONG stay in. The engine
    cannot know an answer is wrong at mint time, so filtering on the
    sealed answer would manufacture a corpus the live system could
    never build."""
    corpus = {}
    for f in sorted(W2.glob("*" + ARM_SUFFIX)):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("status") != "certified" or not r.get("ir"):
                continue
            sid = r.get("src_id") or r.get("id")
            corpus.setdefault(str(sid), {"ir": r["ir"],
                                         "arm": f.stem,
                                         "was_correct": r.get("correct")})
    return corpus


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["repeat", "unique"],
                    required=True)
    ap.add_argument("--threshold", type=float, default=0.62)
    ap.add_argument("--min-conf", type=int, default=2)
    ap.add_argument("--corroborate", action="store_true",
                    help="re-check cache hits against an INDEPENDENT "
                         "cached solve (costs one cheap call)")
    a = ap.parse_args()

    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    from reflex import planir
    from reflex.plancache import PlanCache
    import v10.universe10 as U10

    corrob = {}
    if a.corroborate:
        from reflex.adapters.anthropic_bridge import             AnthropicBridgeAdapter
        from reflex.parse_agent import corroborate as _corr
        bd = HERE / "results" / "bridge_v13"
        adapters = [AnthropicBridgeAdapter(model=m.name,
                                           bridge_dir=m)
                    for m in bd.iterdir() if m.is_dir()]

        def corr_of(q):
            """Cached corroborations only -- never enqueues, so the
            replay stays offline and costs nothing new."""
            for ad in adapters:
                try:
                    v, pend = _corr(ad, q)
                except Exception:
                    continue
                if not pend and v is not None:
                    return v
            return None
        corrob["fn"] = corr_of

    corpus = solved_corpus()
    texts = query_text()
    stream = json.loads((DATA / f"v13_traffic_{a.mode}.json")
                        .read_text(encoding="utf-8"))
    cache = PlanCache(threshold=a.threshold, min_conf=a.min_conf)

    # PRELOAD. Every verified plan enters the cache once, at
    # min_conf=1: a plan that already passed the full gauntlet has
    # been confirmed by the checks themselves, and demanding a second
    # independent sighting of the same SIGNATURE would just re-count
    # how common that signature is. Note what is NOT filtered -- plans
    # the arm later graded wrong stay in, because the engine cannot
    # know that at mint time (B6).
    preload = PlanCache(threshold=a.threshold, min_conf=1)
    minted = wrong_seeded = 0
    for sid, rec in sorted(corpus.items()):
        q = texts.get(sid)
        if not q:
            continue
        if preload.observe(q, rec["ir"]):
            minted += 1
            if rec.get("was_correct") is False:
                wrong_seeded += 1
    cache = preload

    st = Counter()
    fail = Counter()
    rows = []
    curve = []
    for i, it in enumerate(stream):
        sid = str(it.get("id"))
        q = it["q"]
        ans = it.get("answer")
        hit = cache.match(q)
        served = False
        if hit is not None:
            ir, score, sig = hit
            ok, report = planir.verify(ir, ir, q, U10.KINDS10)
            if ok:
                val, _ = planir.execute(ir)
                if val is not None and corrob.get("fn"):
                    cv = corrob["fn"](q)
                    if cv is None:
                        st["corrob_unavailable"] += 1
                        val = None
                    elif abs(cv - val) > 2e-2 * max(1e-9, abs(val)):
                        st["corrob_mismatch"] += 1
                        val = None
                if val is not None:
                    good = grade(val, ans)
                    st["cache_served"] += 1
                    st["cache_correct" if good else "CACHE_WRONG"] += 1
                    rows.append({"i": i, "id": sid, "via": "cache",
                                 "score": round(score, 3), "sig": sig,
                                 "value": val, "answer": ans,
                                 "correct": good})
                    served = True
            if not served:
                st["cache_rejected"] += 1
                fail[next((k for k, v in report.items()
                           if isinstance(v, dict) and not v.get("ok")),
                          "execute")] += 1
        if not served:
            st["escalated"] += 1
        if (i + 1) % 200 == 0:
            curve.append({"n": i + 1,
                          "served": st["cache_served"],
                          "wrong": st["CACHE_WRONG"],
                          "schemas": len(cache.rows)})

    n = len(stream)
    served = st["cache_served"]
    summ = {"mode": a.mode, "n": n, "design": "preloaded-transfer",
            "corpus_verified_plans": len(corpus),
            "schemas_preloaded": minted,
            "schemas_from_wrong_solves": wrong_seeded,
            "threshold": a.threshold, "min_conf": a.min_conf,
            "status": dict(st),
            "cache_hit_rate": round(served / n, 4),
            "cache_accuracy": (round(st["cache_correct"] / served, 4)
                               if served else None),
            "wrong_fire_rate": round(st["CACHE_WRONG"] / max(1, served),
                                     4),
            "rejected_first_check": dict(fail),
            "cache": cache.stats(), "curve": curve}
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = "_corrob" if a.corroborate else ""
    (OUT / f"w5_{a.mode}{suffix}_summary.json").write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    summ["corroborated"] = a.corroborate
    with open(OUT / f"w5_{a.mode}{suffix}.jsonl", "w",
              encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({k: v for k, v in summ.items()
                      if k not in ("cache", "curve")}, indent=1))


if __name__ == "__main__":
    main()
