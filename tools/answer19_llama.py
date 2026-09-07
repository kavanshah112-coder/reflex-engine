# -*- coding: utf-8 -*-
# origin: new for V1.9 -- the independent-family answerer (SPEC 6, Q4)
"""llama-3.1-8B via local ollama answers each batch question with one
number; the frozen answerer prompt (SPEC 12.3). Never sees a reading.

  python tools/answer19_llama.py --phase dev [--model llama3.1:latest]
writes results/v19/bridge/answers_llama_<phase>_NN.json
"""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
BRIDGE = HERE / "results" / "v19" / "bridge"
PROMPT = ("Answer the following question. Reply with ONE number only, "
          "no words, no units, no explanation.\n\nQUESTION: {q}\n\nANSWER:")


def ask(model, q, timeout=120):
    body = json.dumps({"model": model, "prompt": PROMPT.format(q=q),
                       "stream": False,
                       "options": {"temperature": 0, "num_predict": 24}}
                      ).encode("utf-8")
    req = urllib.request.Request("http://localhost:11434/api/generate",
                                 data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8")).get("response", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="dev")
    ap.add_argument("--model", default="llama3.1:latest")
    a = ap.parse_args()
    batches = sorted(BRIDGE.glob("batch_%s_*.json" % a.phase))
    t0 = time.time()
    n = 0
    for b in batches:
        idx = b.stem.split("_")[-1]
        out = BRIDGE / ("answers_llama_%s_%s.json" % (a.phase, idx))
        if out.exists():
            continue
        res = {}
        for it in json.loads(b.read_text(encoding="utf-8")):
            try:
                res[it["id"]] = ask(a.model, it["question"]).strip()[:60]
            except Exception as exc:          # noqa: BLE001
                res[it["id"]] = None
                print("error", it["id"], repr(exc)[:80], file=sys.stderr)
            n += 1
        out.write_text(json.dumps(res, indent=1), encoding="utf-8")
        print(b.name, "done", n, "items", round(time.time() - t0), "s",
              flush=True)


if __name__ == "__main__":
    main()
