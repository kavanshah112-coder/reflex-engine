"""Ollama client for llama3.1:8b — teacher, Mode-A baseline, and hybrid fallback.

All token counts and durations are MEASURED (returned by ollama).
FLOPs are ESTIMATED as 2 * n_params * tokens and must be labeled as such.
"""
import subprocess
import threading
import time

import requests

BASE = "http://localhost:11434"
MODEL = "llama3.1:latest"
N_PARAMS = 8.03e9  # llama3.1-8B parameter count (for FLOPs ESTIMATES only)

SYSTEM_ANSWER = (
    "You are a physics assistant. Answer concisely and precisely. "
    "For numeric problems, give the final number with units. "
    "For derivations, show brief steps and state the final equation. "
    "For conceptual questions, answer in 2-4 sentences.")


def generate(prompt, system=SYSTEM_ANSWER, num_predict=300, temperature=0.0,
             seed=42, timeout=600):
    body = {"model": MODEL, "prompt": prompt, "stream": False,
            "keep_alive": "60m",
            "options": {"num_predict": num_predict, "temperature": temperature,
                        "seed": seed}}
    if system:
        body["system"] = system
    t0 = time.perf_counter()
    r = requests.post(f"{BASE}/api/generate", json=body, timeout=timeout)
    r.raise_for_status()
    d = r.json()
    wall_ms = (time.perf_counter() - t0) * 1000
    pt = d.get("prompt_eval_count", 0)
    gt = d.get("eval_count", 0)
    return {
        "text": d.get("response", ""),
        "prompt_tokens": pt, "gen_tokens": gt,
        "load_ms": d.get("load_duration", 0) / 1e6,
        "prompt_ms": d.get("prompt_eval_duration", 0) / 1e6,
        "gen_ms": d.get("eval_duration", 0) / 1e6,
        "total_ms": d.get("total_duration", 0) / 1e6,
        "wall_ms": wall_ms,
        "flops_est": 2.0 * N_PARAMS * (pt + gt),
    }


def warmup():
    return generate("Say OK.", system=None, num_predict=4)


JUDGE_SYSTEM = (
    "You are a strict physics grader. Compare the candidate answer with the "
    "reference. Reply with exactly one word on the first line: CORRECT or "
    "INCORRECT. A candidate is CORRECT if it conveys the same essential physics "
    "or the same final result, even with different wording.")


def judge(question, reference, candidate):
    prompt = (f"Question: {question}\n\nReference answer: {reference}\n\n"
              f"Candidate answer: {candidate}\n\nVerdict:")
    out = generate(prompt, system=JUDGE_SYSTEM, num_predict=40)
    first = out["text"].strip().split()
    verdict = first[0].upper().strip(".:,") if first else "INCORRECT"
    out["verdict"] = verdict == "CORRECT"
    return out


class GpuPowerSampler:
    """Samples nvidia-smi power.draw in a thread. MEASURED GPU power only —
    CPU package power is not accessible on this machine, so total system energy
    remains an estimate and must be labeled as such."""

    def __init__(self, interval=0.5):
        self.interval = interval
        self.samples = []
        self._stop = threading.Event()
        self._t = None

    def _run(self):
        while not self._stop.is_set():
            try:
                out = subprocess.run(
                    ["nvidia-smi", "--query-gpu=power.draw",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5)
                val = float(out.stdout.strip().splitlines()[0])
                self.samples.append((time.time(), val))
            except Exception:
                pass
            self._stop.wait(self.interval)

    def start(self):
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def stop(self):
        self._stop.set()
        if self._t:
            self._t.join(timeout=2)
        if not self.samples:
            return None
        vals = [v for _, v in self.samples]
        return {"mean_w": sum(vals) / len(vals), "max_w": max(vals),
                "n_samples": len(vals)}
