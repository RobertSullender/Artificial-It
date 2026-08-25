# SPDX-License-Identifier: MIT
import asyncio
import threading
import time
from typing import Callable

class LoopManager:
    def __init__(self):
        self.loop = None
        self._thread = None
        self._stopping = False

    def start(self):
        """Starts the asyncio loop in a separate thread."""
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        # Wait until the loop is actually running
        while self.loop.is_running() is False:
            time.sleep(0.1)

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coro: Callable):
        """Submit a coroutine to the loop from another thread."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def stop(self):
        """Stops the loop and thread."""
        self._stopping = True
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self._thread:
            self._thread.join()

# Singleton-like instance for easy access
instance = LoopManager()
