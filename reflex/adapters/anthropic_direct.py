# -*- coding: utf-8 -*-
# origin: new for V1.0 — direct Anthropic API adapter (user-provided
# key in .env, added 2026-08-29; replaces the deferred-replay bridge
# for the haiku/sonnet A2 scale replications)
"""Direct Anthropic Messages API adapter. Reads ANTHROPIC_API_KEY
from the repo's gitignored .env (or the environment). API models are
NEVER on the joule axis (V1_SPEC §0.5): this adapter reports
calls/tokens only."""
import json
import os
import time
import urllib.request
from pathlib import Path

from .base import Completion, LLMAdapter


def _load_key():
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    env = Path(__file__).resolve().parents[2] / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip(
                    '"').strip("'")
    return None


class AnthropicDirectAdapter(LLMAdapter):
    name = "anthropic_direct"

    def __init__(self, model="claude-haiku-4-5", timeout=120,
                 max_retries=4):
        super().__init__()
        self.model = model
        self.name = f"anthropic:{model}"
        self.timeout = timeout
        self.max_retries = max_retries
        self.key = _load_key()
        if not self.key or "PASTE" in self.key:
            raise RuntimeError("no ANTHROPIC_API_KEY in env/.env")

    def _complete(self, prompt, system, max_tokens):
        body = {"model": self.model, "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]}
        if system:
            body["system"] = system
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(body).encode(),
            headers={"x-api-key": self.key,
                     "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        t0 = time.perf_counter()
        last = None
        for attempt in range(self.max_retries):
            try:
                with urllib.request.urlopen(
                        req, timeout=self.timeout) as r:
                    d = json.loads(r.read())
                text = "".join(b.get("text", "")
                               for b in d.get("content", []))
                u = d.get("usage") or {}
                return Completion(
                    text=text,
                    tokens_in=u.get("input_tokens", 0),
                    tokens_out=u.get("output_tokens", 0),
                    wall_ms=(time.perf_counter() - t0) * 1000)
            except urllib.error.HTTPError as e:
                last = f"{e.code}:{e.read().decode()[:200]}"
                if e.code in (429, 500, 502, 503, 529):
                    time.sleep(2 ** attempt * 2)
                    continue
                raise RuntimeError(f"anthropic api {last}")
            except (urllib.error.URLError, TimeoutError) as e:
                last = str(e)
                time.sleep(2 ** attempt * 2)
        raise RuntimeError(f"anthropic api retries exhausted: {last}")
