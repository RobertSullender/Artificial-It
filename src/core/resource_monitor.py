# SPDX-License-Identifier: MIT
import threading
import psutil
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import pynvml
    _HAS_NVML_MODULE = True
except ImportError:
    _HAS_NVML_MODULE = False

class ResourceMonitor(QThread):
    # Signals to emit data for the UI
    stats_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def run(self):
        initialized = False
        if _HAS_NVML_MODULE:
            try:
                pynvml.nvmlInit()
                initialized = True
            except Exception:
                pass

        try:
            while not self._stop_event.is_set():
                stats = {}
                stats['cpu_percent'] = psutil.cpu_percent(interval=None)

                mem = psutil.virtual_memory()
                stats['ram_percent'] = mem.percent
                stats['ram_used_gb'] = round(mem.used / (1024 ** 3), 2)

                if initialized:
                    try:
                        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        stats['gpu_percent'] = util.gpu
                        stats['gpu_mem_used_gb'] = round(info.used / (1024 ** 3), 2)
                    except Exception:
                        stats['gpu_percent'] = 0
                        stats['gpu_mem_used_gb'] = 0
                else:
                    stats['gpu_percent'] = 0
                    stats['gpu_mem_used_gb'] = 0

                self.stats_updated.emit(stats)
                self._stop_event.wait(1)
        finally:
            if initialized:
                try:
                    pynvml.nvmlShutdown()
                except Exception:
                    pass

    def stop(self):
        self._stop_event.set()
        if self.isRunning() and not self.wait(2000):
            raise RuntimeError("Resource monitor did not stop cleanly")

    def start_monitor(self):
        self._stop_event.clear()
        self.start()