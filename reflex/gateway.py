# -*- coding: utf-8 -*-
# origin: new for V1.0 (public surface per V1_SPEC §3)
"""ReflexGateway — the single public entry point.

P1 skeleton behavior: no certified path exists yet (the reflex layers
arrive in P2), so every query escalates to the plugged-in LLM and the
certificate records why. The ask() contract, statuses, and certificate
shape are final from day one; P2 fills in the reflex path behind them.
"""
import time

from .adapters.base import LLMAdapter
from .answer import (ABSTAINED, CERTIFIED_REFLEX, LLM_ESCALATED, Answer,
                     Certificate, Cost)

ENGINE_VERSION = "1.0-p1"


class ReflexGateway:
    def __init__(self, llm: LLMAdapter, pack=None):
        self.llm = llm
        self.pack = pack           # P2: pack loader replaces None
        self._n = {s: 0 for s in
                   (CERTIFIED_REFLEX, LLM_ESCALATED, ABSTAINED)}

    def ask(self, query: str) -> Answer:
        t0 = time.perf_counter()
        # P2 inserts here: recognition -> parse -> integrity -> worker.
        reason = ("no certified path: reflex layers not yet loaded "
                  "(P1 skeleton)" if self.pack is None else
                  "no certified path for this query")
        c = self.llm.complete(query)
        cost = Cost(llm_calls=1, tokens_in=c.tokens_in,
                    tokens_out=c.tokens_out,
                    wall_ms=(time.perf_counter() - t0) * 1000)
        if c.pending:
            ans = Answer(
                value=None, status=LLM_ESCALATED,
                certificate=Certificate("escalation", {
                    "engine": ENGINE_VERSION, "reason": reason,
                    "llm": self.llm.name,
                    "bridge_pending": c.request_id}),
                cost=cost)
        else:
            ans = Answer(
                value=c.text, status=LLM_ESCALATED,
                certificate=Certificate("escalation", {
                    "engine": ENGINE_VERSION, "reason": reason,
                    "llm": self.llm.name}),
                cost=cost)
        self._n[ans.status] += 1
        return ans

    def stats(self):
        return {"engine": ENGINE_VERSION, "counts": dict(self._n),
                "llm": self.llm.stats()}
