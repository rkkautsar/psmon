import time
from psmon.base import Watcher


class WallTimeLimiter(Watcher):
    watched_attrs = []

    def __init__(self, limit):
        self._limit = limit

    def fallback(self, res):
        return time.monotonic() - self._start_time

    def register_root(self, pid):
        self._start_time = time.monotonic()

    def update(self, processes_info):
        pass

    def get_stats(self, pid):
        return time.monotonic() - self._start_time

    def should_terminate(self, pid):
        return time.monotonic() - self._start_time > self._limit

    def get_error(self, pid):
        return TimeoutError, "Wall time limit exceeded!"
