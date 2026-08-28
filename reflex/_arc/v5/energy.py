"""V0.5 energy meter (Sections 6-8, 33).

Measurement levels, labeled honestly per Section 6:
  GPU  : LEVEL 2 - nvidia-smi power.draw streamed at ~200 ms and integrated
         (trapezoid) over wall-clock query windows. Measured telemetry.
  CPU  : LEVEL 3 - measured process CPU-seconds (psutil, per-process deltas
         for the ollama server tree + this python process) multiplied by a
         DOCUMENTED power model for the i9-13900H package; plus a parallel
         system-utilization accounting net of measured ambient. Modeled, not
         measured electricity - the report must say so.
  FLOPs: LEVEL 4 - carried through from V0.1-V0.4 estimates for continuity.

Every raw sample is persisted (results/raw_v5/energy/*.jsonl) so analysis
and plots regenerate from files (Section 43.8/43.13).

CPU power model (documented, used for cpu_j_model):
  P_active_per_thread(W): the i9-13900H has PL1 = 45 W "processor base
  power" (Intel ARK) sustained across ~20 logical threads under all-core
  load, but single/low-thread boost draws far more per thread. We model
  active power per busy-thread-second as an affine interpolation:
      threads_busy <= 2 : 18 W per busy thread   (boost regime)
      threads_busy >= 14: 45/14 = 3.2 W per busy thread (PL1-bound)
      linear in between.
  Ollama llama.cpp runs all-core (>= 14 busy threads) during generation, so
  its effective coefficient is the PL1-bound one; the reflex python process
  is single-threaded and gets the boost coefficient. A +/-50% sensitivity
  band on this model is carried through the final analysis (Section 32).
Idle/ambient power is measured separately and reported; per-query energy is
reported both GROSS (includes ambient share) and DYNAMIC (above ambient).
"""
import json
import subprocess
import threading
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw_v5" / "energy"

# ---- documented CPU power model constants (see module docstring) ----
CPU_W_BOOST_PER_THREAD = 18.0     # W per busy thread, <=2 threads busy
CPU_ALL_CORE_W = 45.0             # PL1 sustained package power (Intel ARK)
CPU_ALL_CORE_THREADS = 14.0       # threads at which PL1 bound dominates
CPU_IDLE_PKG_W = 4.0              # documented typical idle package power
GPU_IDLE_W_DEFAULT = 6.2          # measured at session start; recalibrated


def cpu_w_per_thread(threads_busy):
    """Affine per-busy-thread power coefficient (see module docstring)."""
    t = max(threads_busy, 0.25)
    if t <= 2:
        return CPU_W_BOOST_PER_THREAD
    hi = CPU_ALL_CORE_W / CPU_ALL_CORE_THREADS
    if t >= CPU_ALL_CORE_THREADS:
        return hi
    # linear from (2, 18) to (14, 3.2)
    f = (t - 2) / (CPU_ALL_CORE_THREADS - 2)
    return CPU_W_BOOST_PER_THREAD + f * (hi - CPU_W_BOOST_PER_THREAD)


def _ollama_procs():
    # the actual compute lives in the runner subprocess `llama-server.exe`,
    # not just `ollama.exe` (verified 2026-08-24 by process watching during
    # a warm generation) — match both stems
    out = []
    for p in psutil.process_iter(["name"]):
        try:
            n = (p.info["name"] or "").lower()
            if "ollama" in n or "llama" in n:
                out.append(p)
        except psutil.Error:
            continue
    return out


class PowerMeter:
    """Streams GPU power + CPU utilization + per-process CPU times.

    Usage:
        m = PowerMeter(tag="bench_main"); m.start()
        with m.window("query_17") as w: ...
        m.stop()
    Each window yields a dict with gpu_j (LEVEL 2), cpu_j_model (LEVEL 3,
    process-attributed), cpu_j_util (LEVEL 3, system-utilization net of
    ambient), wall_s, and the raw process cpu-second deltas.
    """

    def __init__(self, tag, sample_ms=200, raw_dir=RAW):
        self.tag = tag
        self.sample_ms = sample_ms
        self.samples = []          # (t, gpu_w, cpu_pct, freq_mhz)
        self._stop = threading.Event()
        self._threads = []
        self._gpu_proc = None
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.ambient = None        # set by calibrate()
        self._lock = threading.Lock()

    # ---------- sampling ----------
    def _gpu_loop(self):
        cmd = ["nvidia-smi", "--query-gpu=power.draw,utilization.gpu",
               "--format=csv,noheader,nounits", f"-lms", str(self.sample_ms)]
        self._gpu_proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, bufsize=1)
        for line in self._gpu_proc.stdout:
            if self._stop.is_set():
                break
            try:
                w, util = line.strip().split(",")
                with self._lock:
                    self._last_gpu = (time.perf_counter(), float(w),
                                      float(util))
            except (ValueError, AttributeError):
                continue

    def _cpu_loop(self):
        psutil.cpu_percent()  # prime
        while not self._stop.is_set():
            t = time.perf_counter()
            pct = psutil.cpu_percent()
            freq = psutil.cpu_freq()
            g = getattr(self, "_last_gpu", (t, None, None))
            with self._lock:
                self.samples.append(
                    (t, g[1], g[2], pct, freq.current if freq else None))
            time.sleep(self.sample_ms / 1000.0)

    def start(self):
        self._stop.clear()
        self._last_gpu = (time.perf_counter(), None, None)
        for fn in (self._gpu_loop, self._cpu_loop):
            th = threading.Thread(target=fn, daemon=True)
            th.start()
            self._threads.append(th)
        time.sleep(0.6)  # let first samples land

    def stop(self):
        self._stop.set()
        if self._gpu_proc:
            self._gpu_proc.terminate()
        for th in self._threads:
            th.join(timeout=3)
        self._threads = []
        p = self.raw_dir / f"{self.tag}_samples.jsonl"
        with open(p, "w", encoding="utf-8") as f:
            for s in self.samples:
                f.write(json.dumps({"t": s[0], "gpu_w": s[1],
                                    "gpu_util": s[2], "cpu_pct": s[3],
                                    "freq_mhz": s[4]}) + "\n")
        return p

    # ---------- calibration ----------
    def calibrate_ambient(self, seconds=20):
        """Measure ambient (idle-for-us) power before a run stage."""
        t0 = time.perf_counter()
        time.sleep(seconds)
        t1 = time.perf_counter()
        with self._lock:
            win = [s for s in self.samples if t0 <= s[0] <= t1]
        gpu = [s[1] for s in win if s[1] is not None]
        cpu = [s[3] for s in win if s[3] is not None]
        self.ambient = {
            "gpu_w": sum(gpu) / len(gpu) if gpu else GPU_IDLE_W_DEFAULT,
            "cpu_pct": sum(cpu) / len(cpu) if cpu else 0.0,
            "seconds": seconds, "n_samples": len(win)}
        return self.ambient

    # ---------- windows ----------
    def _proc_cpu_seconds(self):
        """(ollama_cpu_s, self_cpu_s) cumulative."""
        oll = 0.0
        for p in _ollama_procs():
            try:
                ct = p.cpu_times()
                oll += ct.user + ct.system
            except psutil.Error:
                continue
        me = psutil.Process()
        ct = me.cpu_times()
        return oll, ct.user + ct.system

    def window(self, label):
        return _Window(self, label)

    def integrate(self, t0, t1, oll_d, self_d, threads_hint_llm=16.0):
        """Compute energy dict for [t0, t1] given process cpu-sec deltas."""
        with self._lock:
            win = [s for s in self.samples if t0 - 0.25 <= s[0] <= t1 + 0.25]
        wall = t1 - t0
        # GPU: trapezoid over samples (LEVEL 2)
        gpu_j = None
        pts = [(s[0], s[1]) for s in win if s[1] is not None]
        if len(pts) >= 2:
            gpu_j = 0.0
            for (ta, wa), (tb, wb) in zip(pts, pts[1:]):
                gpu_j += (wa + wb) / 2 * (tb - ta)
            # extend to full window edges with nearest sample
            gpu_j += pts[0][1] * max(0.0, pts[0][0] - t0)
            gpu_j += pts[-1][1] * max(0.0, t1 - pts[-1][0])
        elif len(pts) == 1:
            gpu_j = pts[0][1] * wall
        amb_gpu = (self.ambient or {}).get("gpu_w", GPU_IDLE_W_DEFAULT)
        gpu_j_dyn = None if gpu_j is None else max(
            0.0, gpu_j - amb_gpu * wall)
        # CPU model A: process-attributed (LEVEL 3, background-immune)
        n_logical = psutil.cpu_count() or 20
        thr_llm = min(threads_hint_llm,
                      max(1.0, oll_d / wall if wall > 0 else 1.0))
        cpu_j_model = (oll_d * cpu_w_per_thread(thr_llm)
                       + self_d * cpu_w_per_thread(
                           min(2.0, self_d / wall if wall > 0 else 1.0)))
        # CPU model B: system utilization net of ambient (LEVEL 3)
        cps = [s[3] for s in win if s[3] is not None]
        cpu_pct = sum(cps) / len(cps) if cps else 0.0
        amb_cpu = (self.ambient or {}).get("cpu_pct", 0.0)
        busy_threads = max(0.0, (cpu_pct - amb_cpu) / 100.0) * n_logical
        cpu_j_util = busy_threads * cpu_w_per_thread(
            max(busy_threads, 0.5)) * wall
        return {"wall_s": wall, "gpu_j": gpu_j, "gpu_j_dyn": gpu_j_dyn,
                "cpu_j_model": cpu_j_model, "cpu_j_util": cpu_j_util,
                "cpu_s_ollama": oll_d, "cpu_s_self": self_d,
                "cpu_pct_mean": cpu_pct, "n_samples": len(win),
                "ambient": self.ambient}


class _Window:
    def __init__(self, meter, label):
        self.meter = meter
        self.label = label
        self.result = None

    def __enter__(self):
        self.t0 = time.perf_counter()
        self.oll0, self.self0 = self.meter._proc_cpu_seconds()
        return self

    def __exit__(self, *exc):
        t1 = time.perf_counter()
        oll1, self1 = self.meter._proc_cpu_seconds()
        self.result = self.meter.integrate(
            self.t0, t1, max(0.0, oll1 - self.oll0),
            max(0.0, self1 - self.self0))
        self.result["label"] = self.label
        return False


def total_j(e, cpu_model="cpu_j_model", dyn=False):
    """Combine one window dict into a single joules figure."""
    if e is None:
        return None
    g = e.get("gpu_j_dyn" if dyn else "gpu_j") or 0.0
    return g + (e.get(cpu_model) or 0.0)
