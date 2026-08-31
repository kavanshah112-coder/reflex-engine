# -*- coding: utf-8 -*-
# origin: new for V1.0 (model-agnostic manager per V0.10 result)
"""LLM adapter contract: one uniform complete() + metering.

The engine is model-agnostic (V0.10: identical behavior under
llama-8B/haiku/sonnet). Adapters expose exactly one generation call and
accumulate call/token counts; nothing above this layer may know which
model is plugged in.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Completion:
    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    wall_ms: float = 0.0
    pending: bool = False        # deferred-bridge adapters only
    request_id: Optional[str] = None


class LLMAdapter:
    """Subclass and implement _complete(). Metering is handled here."""

    name = "base"

    def __init__(self):
        self.calls = 0
        self.tokens_in = 0
        self.tokens_out = 0

    def complete(self, prompt: str, system: Optional[str] = None,
                 max_tokens: int = 512, **kw) -> Completion:
        c = self._complete(prompt, system=system,
                           max_tokens=max_tokens, **kw)
        self.calls += 1
        self.tokens_in += c.tokens_in
        self.tokens_out += c.tokens_out
        return c

    def _complete(self, prompt, system, max_tokens,
                  **kw) -> Completion:
        raise NotImplementedError

    def stats(self):
        return {"adapter": self.name, "calls": self.calls,
                "tokens_in": self.tokens_in,
                "tokens_out": self.tokens_out}
