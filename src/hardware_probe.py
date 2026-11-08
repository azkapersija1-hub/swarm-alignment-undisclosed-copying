"""Hardware probe and GPU sampler (English). Writes HARDWARE_AUDIT.json; GpuSampler logs to JSONL."""
import json
import subprocess
import sys
import threading
import time

QUERY = "name,compute_cap,memory.total,memory.used,temperature.gpu,utilization.gpu,driver_version,power.draw"


def _smi():
    out = subprocess.run(["nvidia-smi", f"--query-gpu={QUERY}", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, check=True).stdout.strip().split(",")
    keys = QUERY.split(",")
    return dict(zip(keys, [x.strip() for x in out]))


def probe():
    info = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "python": sys.version, "gpu": None, "torch": None, "ollama": None}
    try:
        info["gpu"] = _smi()
    except Exception as exc:  # no NVIDIA driver
        info["gpu_error"] = repr(exc)
    try:
        import torch
        info["torch"] = {"version": torch.__version__, "cuda_available": torch.cuda.is_available(),
                         "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}
    except Exception as exc:
        info["torch_error"] = repr(exc)
    try:
        info["ollama"] = subprocess.run(["ollama", "--version"], capture_output=True, text=True).stdout.strip()
    except Exception as exc:
        info["ollama_error"] = repr(exc)
    try:
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                        ("tpf", ctypes.c_ulonglong), ("apf", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong),
                        ("ae", ctypes.c_ulonglong)]
        m = MS(); m.l = ctypes.sizeof(MS); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        info["ram_gb_total"] = round(m.tp / 2**30, 1); info["ram_gb_available"] = round(m.ap / 2**30, 1)
    except Exception as exc:
        info["ram_error"] = repr(exc)
    return info


class GpuSampler:
    """Background sampler: appends one JSON line every `period` seconds; stops when .stop() is called."""

    def __init__(self, path, period=5.0, temp_limit_c=82):
        self.path, self.period, self.temp_limit_c = path, period, temp_limit_c
        self._stop, self.max_temp, self.n = threading.Event(), 0.0, 0
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        with open(self.path, "a", encoding="utf-8") as fh:
            while not self._stop.is_set():
                try:
                    s = _smi(); s["t"] = time.time(); fh.write(json.dumps(s) + "\n"); fh.flush()
                    self.max_temp = max(self.max_temp, float(s["temperature.gpu"])); self.n += 1
                except Exception:
                    pass
                self._stop.wait(self.period)

    def start(self):
        self.thread.start(); return self

    def stop(self):
        self._stop.set(); self.thread.join(timeout=10)

    def too_hot(self):
        try:
            return float(_smi()["temperature.gpu"]) >= self.temp_limit_c
        except Exception:
            return False


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "HARDWARE_AUDIT.json"
    json.dump(probe(), open(out, "w", encoding="utf-8"), indent=1)
    print(open(out, encoding="utf-8").read())
