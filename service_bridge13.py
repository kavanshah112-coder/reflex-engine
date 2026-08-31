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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRIDGE = HERE / "results" / "bridge_v13"
BATCH = 100   # V1.1 lesson: large single-file writes fail (64k output limit)


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
            rows = json.loads(rf.read_text(encoding="utf-8"))
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
