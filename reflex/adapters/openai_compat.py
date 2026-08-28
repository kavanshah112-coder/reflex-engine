# -*- coding: utf-8 -*-
# origin: new for V1.0 (generic third-party plug per V1_SPEC §3)
"""OpenAI-compatible chat-completions adapter (works against any
/v1/chat/completions endpoint, incl. ollama's compat layer)."""
import json
import os
import time
import urllib.request

from .base import Completion, LLMAdapter


class OpenAICompatAdapter(LLMAdapter):
    name = "openai_compat"

    def __init__(self, model="llama3.1:latest",
                 base_url="http://localhost:11434/v1",
                 api_key=None, temperature=0.0, timeout=180):
        super().__init__()
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.temperature = temperature
        self.timeout = timeout

    def _complete(self, prompt, system, max_tokens):
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        body = {"model": self.model, "messages": msgs,
                "temperature": self.temperature,
                "max_tokens": max_tokens}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(body).encode(), headers=headers)
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            d = json.loads(r.read())
        usage = d.get("usage") or {}
        return Completion(
            text=d["choices"][0]["message"]["content"],
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            wall_ms=(time.perf_counter() - t0) * 1000)
