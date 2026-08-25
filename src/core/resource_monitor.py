# SPDX-License-Identifier: MIT
import sys
import time
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
        self._running = True

    def run(self):
        initialized = False
        if _HAS_NVML_MODULE:
            try:
                pynvml.nvmlInit()
                initialized = True
            except Exception:
                pass

        while self._running:
            stats = {}
            # CPU Usage
            stats['cpu_percent'] = psutil.cpu_percent(interval=None)
            
            # RAM Usage
            mem = psutil.virtual_memory()
            stats['ram_percent'] = mem.percent
            stats['ram_used_gb'] = round(mem.used / (1024 ** 3), 2)

            # GPU Usage (NVIDIA only via NVML)
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
            time.sleep(1)  # Update every second

    def stop(self):
        self._running = False
        if _HAS_NVML_MODULE:
            try:
                pynvml.nvmlShutdown()
            except:
                pass
        self.terminate() # Force stop for simplicity in this initial version