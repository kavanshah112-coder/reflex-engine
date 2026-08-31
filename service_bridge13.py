# -*- coding: utf-8 -*-
# origin: new for V1.3 — batched bridge protocol (V1_3_SPEC §2)
"""Bridge servicing at ~10x V1.2's throughput.

V1.2 gave each agent 40 request FILES and took 40 response files back:
~80 tool calls and ~100k context to move 40 prompts. Here an agent
reads ONE batch file containing the prompts inline and writes ONE
result file — two tool calls for 200 prompts.

  python service_bridge13.py list   <model>   # pending -> batch files
  python service_bridge13.py ingest <model>   # results -> adapter cache
  python service_bridge13.py status <model>

`ingest` explodes the agent's single result file into the per-key
resp_*.json files the adapter already understands, so nothing
downstream changes. Stub rejection happens here: an empty answer, a
missing key, or non-JSON where the prompt demanded JSON is refused and
left pending rather than silently cached.
"""
import json
import re
import sys
from pathlib import Path

# B11: a refusal is a legitimate answer ONLY when it names something
# about the problem. These reasons name something about the AGENT --
# they are stubs wearing the schema's refuse shape, and because they
# are well-formed JSON the original stub filter waved them through.
STUB_REFUSALS = re.compile(
    r"cannot parse|unable to parse|problem text is empty|"
    r"no problem|empty problem|no numbers found|not provided|"
    r"no text|missing text|could not process|unparseable",
    re.I)

HERE = Path(__file__).resolve().parent
BRIDGE = HERE / "results" / "bridge_v13"
BATCH = 50    # B13: 100-item document-heavy batches exceed agent budget


def pending(model):
    d = BRIDGE / model
    if not d.exists():
        return []
    return sorted(p for p in d.glob("req_*.json")
                  if not (d / f"resp_{p.stem[4:]}.json").exists())


def do_list(model):
    reqs = pending(model)
    bdir = BRIDGE / model / "batches"
    bdir.mkdir(parents=True, exist_ok=True)
    for old in bdir.glob("batch_*.json"):
        old.unlink()
    # B14: the two halves of a dual parse are the SAME prompt under
    # different cache salts. If both land in one batch, a single
    # servicing agent sees the duplicate and answers it identically,
    # and the AGREEMENT check -- the pipeline's strongest
    # discriminator on real language (D7) -- becomes vacuous for that
    # item. This is B3 returning through the batching layer rather
    # than the cache layer. Interleaving by prompt guarantees twins
    # are at least BATCH apart, so they reach different agents.
    byprompt = {}
    for r in reqs:
        try:
            pr = json.loads(r.read_text(encoding="utf-8"))["prompt"]
        except Exception:
            pr = r.stem
        byprompt.setdefault(pr, []).append(r)
    ordered, rnd = [], 0
    while True:
        wave = [v[rnd] for v in byprompt.values() if len(v) > rnd]
        if not wave:
            break
        ordered.extend(wave)
        rnd += 1
    reqs = ordered

    n = 0
    for bi in range(0, len(reqs), BATCH):
        chunk = reqs[bi:bi + BATCH]
        payload = []
        for p in chunk:
            d = json.loads(p.read_text(encoding="utf-8"))
            payload.append({"key": p.stem[4:],
                            "prompt": d["prompt"],
                            "max_tokens": d.get("max_tokens", 900)})
        (bdir / f"batch_{bi // BATCH:03d}.json").write_text(
            json.dumps(payload, indent=1), encoding="utf-8")
        n += 1
    print(f"{model}: {len(reqs)} pending -> {n} batch files "
          f"({BATCH}/batch) in {bdir}")
    return n


def do_ingest(model):
    d = BRIDGE / model
    rdir = d / "results"
    if not rdir.exists():
        print(f"{model}: no results dir")
        return
    wrote = rejected = 0
    for rf in sorted(rdir.glob("*.json")):
        try:
            rows = json.loads(rf.read_text(encoding="utf-8-sig"))
        except Exception as e:
            print(f"  unreadable {rf.name}: {e}")
            continue
        if isinstance(rows, dict):
            rows = rows.get("results") or rows.get("answers") or []
        for row in rows:
            k = row.get("key")
            txt = (row.get("text") or "").strip()
            if not k or not txt:
                rejected += 1
                continue
            req = d / f"req_{k}.json"
            if not req.exists():
                rejected += 1
                continue
            rq = json.loads(req.read_text(encoding="utf-8"))
            if "JSON only" in rq.get("prompt", "") and "{" not in txt:
                rejected += 1      # stub: JSON demanded, none given
                continue
            m = re.search(r'"refuse"\s*:\s*"([^"]{0,200})', txt)
            if m and STUB_REFUSALS.search(m.group(1)):
                rejected += 1      # B11: stub wearing a refusal
                continue
            # B13: a prompt that demanded a bare number and got no
            # digit back was not answered. Agents reach for
            # "UNKNOWN", "N/A", "cannot determine" when they run out
            # of budget, and every one of those would otherwise be
            # ingested as a real model response.
            if "ONLY the final number" in rq.get("prompt", "")                     and not re.search(r"\d", txt):
                rejected += 1
                continue
            # B15: an EMPTY JSON object is the last stub shape. It is
            # valid JSON, it contains "{", and it says nothing. One
            # agent filled 33 of 50 slots with it and reported the
            # batch complete.
            if "JSON only" in rq.get("prompt", ""):
                try:
                    obj = json.loads(txt[txt.index("{"):
                                         txt.rindex("}") + 1])
                except Exception:
                    obj = None
                if isinstance(obj, dict) and not any(
                        k in obj for k in ("quantities", "plan",
                                           "refuse")):
                    rejected += 1
                    continue
            (d / f"resp_{k}.json").write_text(json.dumps({
                "text": txt,
                "tokens_in": row.get("tokens_in", 0),
                "tokens_out": row.get("tokens_out", 0)}),
                encoding="utf-8")
            wrote += 1
    print(f"{model}: ingested {wrote}, rejected {rejected}, "
          f"still pending {len(pending(model))}")


if __name__ == "__main__":
    cmd, model = sys.argv[1], sys.argv[2]
    if cmd == "list":
        do_list(model)
    elif cmd == "ingest":
        do_ingest(model)
    else:
        print(f"{model}: {len(pending(model))} pending")
