from collections import defaultdict, namedtuple
from psmon.base import Watcher


class MaxMemoryLimiter(Watcher):
    watched_attrs = ["memory_info"]

    def __init__(self, limit):
        self._limit = limit
        self._known_pids = set()
        self._root = None
        self._tree = defaultdict(list)
        self._max_memory = {}

    def register_root(self, pid):
        self._root = pid

    def _update(self, root, by_pid):
        if root not in by_pid or by_pid[root]["memory_info"] is None:
            return self._max_memory[root]
        max_mem = by_pid[root]["memory_info"].rss
        for child in self._tree[root]:
            max_mem += self._update(child, by_pid)
        self._max_memory[root] = max(self._max_memory[root], max_mem)
        return self._max_memory[root]

    def update(self, processes_info):
        by_pid = {}
        for pinfo in processes_info:
            pid = pinfo["pid"]
            by_pid[pid] = pinfo
            if pid not in self._known_pids:
                self._known_pids.add(pid)
                self._tree[pinfo["ppid"]].append(pid)
                self._max_memory[pid] = 0
        self._update(self._root, by_pid)

    def fallback(self, res):
        return res.ru_maxrss

    def get_stats(self, pid):
        return self._max_memory[pid]

    def should_terminate(self, pid):
        return self.get_stats(pid) > self._limit

    def get_error(self, pid):
        return (MemoryError, "Max memory limit exceeded!")
