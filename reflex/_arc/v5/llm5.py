"""V0.5 optimized-LLM profiles (Sections 4-A, 14, 15, 16).

The V0.5 baseline must be the strongest PRACTICAL optimized configuration of
the locally available model (llama3.1:8b, q4_K_M — the model is already
4-bit quantized; no other quantization is available locally and no model
downloads are performed in this environment, disclosed in the report).

Profiles (all on the SAME model file):
  ref        the pre-existing ollama service config (port 11434) exactly as
             V0.1-V0.4 used it: defaults, num_ctx 4096, no flash attention.
  opt        dedicated server: OLLAMA_FLASH_ATTENTION=1, KV cache q8_0,
             num_ctx=1024 (our prompts are <400 tokens), keep_alive=-1,
             thread count tuned on 3 calibration prompts (validation-style
             text only). Smaller KV => more transformer layers fit in the
             4 GB GPU => measured speed/energy win (calibrated, not assumed).
  cpu        dedicated server, num_gpu=0: CPU-only inference. This is the
             second "hardware configuration" of Section 15.
  opt_b4     opt + OLLAMA_NUM_PARALLEL=4 for the batching experiment
             (Section 16).

Switching profiles unloads the model from every other server first (the
4 GB GPU cannot hold two copies) and re-warms the target, so measured
windows never contain another profile's residual load.

All generate() calls are routed through the active profile by monkey-
patching src.llm.ollama_client.generate — v4's llm_bridge and engines then
transparently use the active profile.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "v0_1"))
from src.llm import ollama_client as base_client  # noqa: E402

MODEL = base_client.MODEL
N_PARAMS = base_client.N_PARAMS

PROFILES = {
    "ref": {"port": 11434, "managed": False, "env": {}, "opts": {}},
    "opt": {"port": 11435, "managed": True,
            "env": {"OLLAMA_FLASH_ATTENTION": "1",
                    "OLLAMA_KV_CACHE_TYPE": "q8_0",
                    "OLLAMA_KEEP_ALIVE": "-1",
                    "OLLAMA_NUM_PARALLEL": "1"},
            "opts": {"num_ctx": 1024}},
    "cpu": {"port": 11437, "managed": True,
            "env": {"OLLAMA_FLASH_ATTENTION": "1",
                    "OLLAMA_KV_CACHE_TYPE": "q8_0",
                    "OLLAMA_KEEP_ALIVE": "-1",
                    "OLLAMA_NUM_PARALLEL": "1"},
            "opts": {"num_ctx": 1024, "num_gpu": 0}},
    "opt_b4": {"port": 11438, "managed": True,
               "env": {"OLLAMA_FLASH_ATTENTION": "1",
                       "OLLAMA_KV_CACHE_TYPE": "q8_0",
                       "OLLAMA_KEEP_ALIVE": "-1",
                       "OLLAMA_NUM_PARALLEL": "4"},
               "opts": {"num_ctx": 1024}},
    # round-2 calibration outcome: flash attention MEASURED as a loss on
    # this 4GB partial-offload GPU; the context-shrunk no-FA server is the
    # real optimization candidate
    "ctx": {"port": 11439, "managed": True,
            "env": {"OLLAMA_KEEP_ALIVE": "-1",
                    "OLLAMA_NUM_PARALLEL": "1"},
            "opts": {"num_ctx": 1024}},
    "ctx_b4": {"port": 11440, "managed": True,
               "env": {"OLLAMA_KEEP_ALIVE": "-1",
                       "OLLAMA_NUM_PARALLEL": "4"},
               "opts": {"num_ctx": 1024}},
}

_servers = {}          # name -> subprocess.Popen
_active = None
_orig_generate = base_client.generate


def _base(profile):
    return f"http://127.0.0.1:{PROFILES[profile]['port']}"


def _alive(profile, timeout=2):
    try:
        r = requests.get(_base(profile) + "/api/version", timeout=timeout)
        return r.ok
    except requests.RequestException:
        return False


def _start_server(profile):
    spec = PROFILES[profile]
    if _alive(profile):
        return
    env = dict(os.environ)
    env.update(spec["env"])
    env["OLLAMA_HOST"] = f"127.0.0.1:{spec['port']}"
    p = subprocess.Popen(["ollama", "serve"], env=env,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    _servers[profile] = p
    for _ in range(60):
        if _alive(profile):
            return
        time.sleep(0.5)
    raise RuntimeError(f"ollama server for profile {profile} did not start")


def _unload(profile):
    """Force-unload the model from a server so VRAM is free."""
    if not _alive(profile):
        return
    try:
        requests.post(_base(profile) + "/api/generate",
                      json={"model": MODEL, "keep_alive": 0},
                      timeout=30)
    except requests.RequestException:
        pass


def _loaded_anywhere():
    out = {}
    for name in PROFILES:
        if _alive(name):
            try:
                r = requests.get(_base(name) + "/api/ps", timeout=3)
                out[name] = [m.get("name") for m in r.json().get(
                    "models", [])]
            except requests.RequestException:
                out[name] = None
    return out


def generate_on(profile, prompt, system=base_client.SYSTEM_ANSWER,
                num_predict=300, temperature=0.0, seed=42, timeout=900,
                extra_opts=None, fmt=None):
    spec = PROFILES[profile]
    opts = {"num_predict": num_predict, "temperature": temperature,
            "seed": seed}
    opts.update(spec["opts"])
    if extra_opts:
        opts.update(extra_opts)
    ka = spec["env"].get("OLLAMA_KEEP_ALIVE", "60m")
    body = {"model": MODEL, "prompt": prompt, "stream": False,
            "keep_alive": -1 if ka == "-1" else ka,
            "options": opts}
    if system:
        body["system"] = system
    if fmt:
        body["format"] = fmt
    t0 = time.perf_counter()
    r = requests.post(_base(profile) + "/api/generate", json=body,
                      timeout=timeout)
    r.raise_for_status()
    d = r.json()
    wall_ms = (time.perf_counter() - t0) * 1000
    pt = d.get("prompt_eval_count", 0)
    gt = d.get("eval_count", 0)
    return {"text": d.get("response", ""), "prompt_tokens": pt,
            "gen_tokens": gt,
            "load_ms": d.get("load_duration", 0) / 1e6,
            "prompt_ms": d.get("prompt_eval_duration", 0) / 1e6,
            "gen_ms": d.get("eval_duration", 0) / 1e6,
            "total_ms": d.get("total_duration", 0) / 1e6,
            "wall_ms": wall_ms, "profile": profile,
            "flops_est": 2.0 * N_PARAMS * (pt + gt)}


def activate(profile, warm=True, extra_opts=None):
    """Make `profile` the active LLM for ALL v4/v5 code paths."""
    global _active
    if profile not in PROFILES:
        raise KeyError(profile)
    if PROFILES[profile]["managed"]:
        _start_server(profile)
    # free the 4GB GPU from every OTHER server before this one loads
    for other in PROFILES:
        if other != profile:
            _unload(other)
    time.sleep(1.0)

    def patched(prompt, system=base_client.SYSTEM_ANSWER, num_predict=300,
                temperature=0.0, seed=42, timeout=900):
        return generate_on(profile, prompt, system=system,
                           num_predict=num_predict, temperature=temperature,
                           seed=seed, timeout=timeout,
                           extra_opts=extra_opts)
    base_client.generate = patched
    base_client.BASE = _base(profile)
    # v4.llm_bridge has its OWN base url + json generator — repoint them so
    # every structured handoff also runs on the active profile
    from v4 import llm_bridge as B4

    def patched_json(prompt, num_predict=220, seed=42):
        return generate_on(profile, prompt, system=None,
                           num_predict=num_predict, seed=seed, fmt="json",
                           extra_opts=extra_opts)
    B4.BASE = _base(profile)
    B4.generate_json = patched_json
    _active = profile
    if warm:
        out = generate_on(profile, "Say OK.", system=None, num_predict=4,
                          extra_opts=extra_opts)
        return out
    return None


def activate_best(warm=True):
    """Activate the calibration-chosen profile incl. its extra options."""
    p = Path(__file__).resolve().parents[1] / "results" / "raw_v5" / \
        "profile_choice.json"
    if p.exists():
        d = json.loads(p.read_text())
        return activate(d["best"], warm=warm,
                        extra_opts=d.get("extra_opts"))
    return activate("ref", warm=warm)


def active():
    return _active


def cold_start_measure(profile, meter):
    """Section 12: measured cold-start — unload everywhere, then time+meter
    the first real call (includes model load)."""
    for name in PROFILES:
        _unload(name)
    time.sleep(3.0)
    with meter.window(f"cold_start_{profile}") as w:
        out = generate_on(profile, "Say OK.", system=None, num_predict=4)
    return {"profile": profile, "load_ms": out["load_ms"],
            "total_ms": out["total_ms"], "energy": w.result}


def shutdown_managed():
    for name, p in _servers.items():
        _unload(name)
        try:
            p.terminate()
        except OSError:
            pass
    _servers.clear()


if __name__ == "__main__":
    # quick self-test: bring up opt server, one warm call each profile
    print("loaded:", json.dumps(_loaded_anywhere()))
    for prof in ["ref", "opt"]:
        w = activate(prof)
        out = generate_on(prof, "What is 17*23? Answer with the number.",
                          num_predict=20)
        print(prof, "->", out["text"].strip()[:40], "| gen_ms",
              round(out["gen_ms"]), "| tok/s",
              round(out["gen_tokens"] / max(out["gen_ms"], 1) * 1000, 1))
