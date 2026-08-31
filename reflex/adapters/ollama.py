# -*- coding: utf-8 -*-
# origin: arc-standard local model access (V0.1+ used ollama llama3.1:8b)
"""Ollama adapter — the arc's metered local model."""
import json
import time
import urllib.request

from .base import Completion, LLMAdapter


class OllamaAdapter(LLMAdapter):
    name = "ollama"

    def __init__(self, model="llama3.1:latest",
                 base_url="http://localhost:11434",
                 temperature=0.0, seed=1, timeout=600):
        super().__init__()
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.seed = seed
        self.timeout = timeout

    def _complete(self, prompt, system, max_tokens, seed=None,
                  temperature=None):
        # V1.3: seed/temperature overridable per call so DUAL-PARSE is
        # two genuinely independent samples. At temperature 0 both
        # parses are byte-identical and the agreement check is
        # vacuous; a fixed seed keeps each sample reproducible.
        body = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": (self.temperature
                                        if temperature is None
                                        else temperature),
                        "seed": self.seed if seed is None else seed,
                        "num_predict": max_tokens},
        }
        if system:
            body["system"] = system
        req = urllib.request.Request(
            self.base_url + "/api/generate",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"})
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            d = json.loads(r.read())
        return Completion(
            text=d.get("response", ""),
            tokens_in=d.get("prompt_eval_count", 0) or 0,
            tokens_out=d.get("eval_count", 0) or 0,
            wall_ms=(time.perf_counter() - t0) * 1000)
