# -*- coding: utf-8 -*-
# origin: deferred-replay bridge pattern from v0.7+ (v7.models lineage)
"""Anthropic adapter via the arc's deferred-replay bridge.

Direct API keys are not available in this environment (workspace keys
REVOKED), so Anthropic-model completions run through the file bridge
the arc used from V0.7 on: requests are enqueued as req_*.json, a
servicing pass (Claude Code Agent tool, matching model) writes
resp_*.json, and replay returns the completion. Deterministic replay:
identical prompt -> identical stored response.

Modes:
  deferred (default): complete() enqueues and returns pending=True if
      no stored response exists; returns the stored completion if it
      does. The caller replays after servicing.
  strict: raise if no stored response (used by replay harnesses).
"""
import hashlib
import json
import time
from pathlib import Path

from .base import Completion, LLMAdapter


class AnthropicBridgeAdapter(LLMAdapter):
    name = "anthropic_bridge"

    def __init__(self, model="claude-haiku-4-5", bridge_dir=None,
                 mode="deferred"):
        super().__init__()
        self.model = model
        self.mode = mode
        self.dir = Path(bridge_dir or
                        Path(__file__).resolve().parents[2] /
                        "results" / "bridge" / model)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _key(self, prompt, system, max_tokens, key_salt=""):
        # V1.3: key_salt participates in the cache key but is NEVER
        # sent to the servicing agent, so DUAL-PARSE gets two
        # independent answers to the same prompt instead of one
        # cached answer returned twice.
        h = hashlib.sha256()
        h.update(json.dumps([self.model, system or "", prompt,
                             max_tokens, key_salt]).encode())
        return h.hexdigest()[:16]

    def _complete(self, prompt, system, max_tokens, key_salt="",
                  **kw):
        k = self._key(prompt, system, max_tokens, key_salt)
        resp = self.dir / f"resp_{k}.json"
        if resp.exists():
            d = json.loads(resp.read_text(encoding="utf-8"))
            return Completion(text=d["text"],
                              tokens_in=d.get("tokens_in", 0),
                              tokens_out=d.get("tokens_out", 0))
        req = self.dir / f"req_{k}.json"
        if not req.exists():
            req.write_text(json.dumps(
                {"model": self.model, "system": system or "",
                 "prompt": prompt, "max_tokens": max_tokens,
                 "queued_at": time.time()}, indent=1),
                encoding="utf-8")
        if self.mode == "strict":
            raise RuntimeError(f"bridge: no response for {k} "
                               f"({self.model}); service the queue")
        return Completion(text="", pending=True, request_id=k)

    def pending(self):
        return sorted(p.stem[4:] for p in self.dir.glob("req_*.json")
                      if not (self.dir /
                              f"resp_{p.stem[4:]}.json").exists())
