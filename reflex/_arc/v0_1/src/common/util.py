"""Shared utilities: seeding, IO, timing, FLOPs accounting."""
import json
import os
import random
import time
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"

GLOBAL_SEED = 42


def set_seed(seed: int = GLOBAL_SEED):
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def save_json(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_jsonl(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def load_jsonl(path):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


class Timer:
    """Wall-clock timer (perf_counter). Measured, not estimated."""

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.elapsed = time.perf_counter() - self.t0

    @property
    def ms(self):
        return self.elapsed * 1000.0


def mlp_forward_flops(layer_dims):
    """Exact multiply-accumulate FLOPs (2*MACs) for a stack of Linear layers.

    layer_dims: list of (in_features, out_features).
    This is ANALYTIC-EXACT for the linear algebra; activation-function cost ignored
    (negligible at these sizes).
    """
    return sum(2 * i * o for i, o in layer_dims)


def transformer_flops_estimate(n_params, n_tokens):
    """ESTIMATED FLOPs for a transformer forward pass: ~2 * params * tokens.

    Standard approximation (Kaplan et al.); ignores attention quadratic term,
    acceptable at short sequence lengths. Always label results using this as ESTIMATED.
    """
    return 2.0 * n_params * n_tokens


def hardware_info():
    import platform
    import psutil
    info = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "cpu_count_logical": psutil.cpu_count(),
        "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
    }
    try:
        import torch
        info["torch"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["gpu"] = torch.cuda.get_device_name(0)
    except ImportError:
        pass
    return info
