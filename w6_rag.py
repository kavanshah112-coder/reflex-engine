# -*- coding: utf-8 -*-
# origin: new for V1.3 -- W6 RAG integration (V1_3_SPEC section 9)
"""Three ways to answer a document question, measured on two corpora.

  python w6_rag.py --corpus generic --arm r3
  python w6_rag.py --corpus user    --arm r1 --model claude-haiku-4-5

  R1 RAG-alone          the model retrieves and computes; the answer
                        is whatever it says
  R2 reflex-in-context  the engine certifies the inputs and injects
                        them as text; the model still writes the
                        answer
  R3 reflex-served      the engine's value IS the answer; any prose is
                        decoration and carries no authority

The pre-declared expectation in section 9 is that R2 improves accuracy
over R1 but forfeits certification -- a model can ignore or mangle
what sits in its context -- while R3 keeps it. R2 exists precisely to
be the tempting middle option that does not work, and it is measured
rather than argued about.

FACTUAL queries are certified on provenance (reflex/provenance.py) and
need no model at all in R3; DERIVED queries still need a reading, so
the parse/verify split applies with the retrieved snippets as the
evidence text: quantities must appear in the RETRIEVED DOCUMENTS, not
merely in the question.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
CORP = HERE / "results" / "v13" / "corpora"
OUT = HERE / "results" / "v13" / "w6"
BRIDGE = HERE / "results" / "bridge_v13"

R1_TMPL = ("Use ONLY these documents to answer.\n\n{docs}\n\n"
           "QUESTION: {q}\n\n"
           "Reply with ONLY the final number, no words, no units.")

R2_TMPL = ("Use ONLY these documents to answer.\n\n{docs}\n\n"
           "VERIFIED VALUES (certified by a deterministic engine; "
           "these supersede anything above):\n{certified}\n\n"
           "QUESTION: {q}\n\n"
           "Reply with ONLY the final number, no words, no units.")


def grade(v, a, tol=2e-2):
    if v is None or a is None:
        return False
    try:
        v, a = float(v), float(a)
    except (TypeError, ValueError):
        return False
    return abs(v) < 1e-9 if a == 0 else abs(v - a) / abs(a) <= tol


class Retriever:
    """Hashed n-gram retrieval -- the arc's own machinery (V0.2
    lineage), no embedder, no model, no external service."""

    def __init__(self, docs):
        from reflex.frame import features
        self.docs = docs
        self.vecs = [features(d["title"] + " " + d["text"])
                     for d in docs]

    def top(self, query, k=6):
        from reflex.frame import cosine, features
        v = features(query)
        scored = sorted(((cosine(v, w), i)
                         for i, w in enumerate(self.vecs)),
                        reverse=True)
        return [self.docs[i] for _, i in scored[:k]]


def render(docs, limit=6):
    return "\n\n".join("[%s v%d, valid %s..%s]\n%s"
                       % (d["id"], d["version"], d["valid_from"],
                          d["valid_to"], d["text"].strip())
                       for d in docs[:limit])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["generic", "user"],
                    required=True)
    ap.add_argument("--arm", choices=["r1", "r2", "r3"], required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--topk", type=int, default=6)
    a = ap.parse_args()

    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    from reflex import planir, provenance
    from reflex.parse_agent import build_prompt, extract_json
    import v10.universe10 as U10

    docs = json.loads((CORP / ("%s_docs.json" % a.corpus))
                      .read_text(encoding="utf-8"))
    qs = json.loads((CORP / ("%s_queries.json" % a.corpus))
                    .read_text(encoding="utf-8"))
    if a.limit:
        qs = qs[:a.limit]
    R = Retriever(docs)

    adapter = None
    if a.arm in ("r1", "r2") or True:
        if a.model:
            from reflex.adapters.anthropic_bridge import \
                AnthropicBridgeAdapter
            adapter = AnthropicBridgeAdapter(
                model=a.model, bridge_dir=BRIDGE / a.model)

    st = Counter()
    rows = []
    for q in qs:
        got = R.top(q["q"], a.topk)
        st["retrieval_hit" if all(n in [d["id"] for d in got]
                                  for n in q["needs"])
           else "retrieval_miss"] += 1
        rec = {"id": q["id"], "family": q["family"],
               "answer": q["answer"], "value": None,
               "status": None, "retrieved": [d["id"] for d in got]}

        if a.arm == "r3" and q["family"] == "factual":
            r = provenance.resolve(got, q["key"],
                                   subject=q["title"])
            if r["ok"]:
                rec["value"] = r["value"]
                rec["provenance"] = r["provenance"]
                rec["status"] = "certified"
            else:
                rec["status"] = "abstained"
                rec["why"] = r["why"]
        elif a.arm == "r3":
            if adapter is None:
                rec["status"] = "skipped_no_model"
            else:
                ev = q["q"] + "\n\nRETRIEVED DOCUMENTS:\n" \
                     + render(got)
                c = adapter.complete(build_prompt(ev, None),
                                     max_tokens=900, seed=1000,
                                     temperature=0.6, key_salt="w6a")
                c2 = adapter.complete(build_prompt(ev, None),
                                      max_tokens=900, seed=1001,
                                      temperature=0.6,
                                      key_salt="w6b")
                if getattr(c, "pending", False) or \
                        getattr(c2, "pending", False):
                    rec["status"] = "pending"
                else:
                    ir1, ir2 = extract_json(c.text), extract_json(c2.text)
                    ok, rep = planir.verify(ir1, ir2, ev, U10.KINDS10)
                    rec["checks"] = rep
                    if not ok:
                        rec["status"] = "verification_failed"
                    else:
                        val, _ = planir.execute(ir1)
                        rec["value"] = val
                        rec["status"] = ("certified" if val is not None
                                         else "execution_failed")
        else:
            if adapter is None:
                rec["status"] = "skipped_no_model"
            else:
                if a.arm == "r1":
                    prompt = R1_TMPL.format(docs=render(got), q=q["q"])
                else:
                    lines = []
                    for d in got[:a.topk]:
                        for k, v in provenance.read_facts(
                                d["text"]).items():
                            r = provenance.resolve(
                                got, k, subject=provenance.base_title(d))
                            if r["ok"]:
                                lines.append("  %s = %s  [%s]"
                                             % (k, r["value"],
                                                r["provenance"]["source"]))
                    seen, uniq = set(), []
                    for ln in lines:
                        if ln not in seen:
                            seen.add(ln)
                            uniq.append(ln)
                    prompt = R2_TMPL.format(
                        docs=render(got), q=q["q"],
                        certified="\n".join(uniq) or "  (none)")
                c = adapter.complete(prompt, max_tokens=32, seed=1000,
                                     temperature=0.3,
                                     key_salt="w6" + a.arm)
                if getattr(c, "pending", False):
                    rec["status"] = "pending"
                else:
                    import re
                    m = re.findall(r"-?\d[\d,]*(?:\.\d+)?",
                                   (c.text or "").replace(",", ""))
                    rec["value"] = float(m[-1]) if m else None
                    rec["status"] = ("answered" if m else "no_answer")

        rec["correct"] = grade(rec["value"], q["answer"])
        st[rec["status"]] += 1
        if rec["status"] in ("certified", "answered"):
            st["correct" if rec["correct"] else "WRONG"] += 1
        rows.append(rec)

    served = st["certified"] + st["answered"]
    # A limited run and a full run are different measurements and
    # must not share a filename: the first W6 pass silently
    # overwrote the full-corpus R3 result (n=300) with a 120-item
    # sample of itself.
    tag = "%s_%s%s" % (a.corpus, a.arm,
                       ("_n%d" % a.limit) if a.limit else "")
    OUT.mkdir(parents=True, exist_ok=True)
    summ = {"corpus": a.corpus, "arm": a.arm, "model": a.model,
            "n": len(qs), "topk": a.topk, "status": dict(st),
            "served": served,
            "coverage": round(served / max(1, len(qs)), 4),
            "accuracy_of_served": (round(st["correct"] / served, 4)
                                   if served else None),
            "wrong_rate_of_served": (round(st["WRONG"] / served, 4)
                                     if served else None),
            "retrieval_recall": round(
                st["retrieval_hit"] / max(1, len(qs)), 4)}
    by_fam = {}
    for fam in ("factual", "derived"):
        f = [r for r in rows if r["family"] == fam]
        s = [r for r in f if r["status"] in ("certified", "answered")]
        by_fam[fam] = {
            "n": len(f), "served": len(s),
            "correct": sum(1 for r in s if r["correct"]),
            "WRONG": sum(1 for r in s if not r["correct"])}
    summ["by_family"] = by_fam
    if a.model:
        summ["token_source"] = "synthetic-bridge"   # B7
        summ["bridge_pending"] = len(adapter.pending())
    (OUT / ("w6_%s_summary.json" % tag)).write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    with open(OUT / ("w6_%s.jsonl" % tag), "w",
              encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    print(json.dumps(summ, indent=1))
    if a.model and summ.get("bridge_pending"):
        print("\nBRIDGE PENDING %d" % summ["bridge_pending"])
        sys.exit(3)


if __name__ == "__main__":
    main()
