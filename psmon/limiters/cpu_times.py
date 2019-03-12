from collections import defaultdict, namedtuple
from psmon.base import Watcher


class CpuTimeLimiter(Watcher):
    watched_attrs = ["cpu_times"]

    def __init__(self, limit):
        self._limit = limit
        self._known_pids = set()
        self._root = None
        self._tree = defaultdict(list)
        self._cpu_times = {}

    def register_root(self, pid):
        self._root = pid

    def _update(self, root, by_pid):
        if root not in by_pid or by_pid[root]["cpu_times"] is None:
            return self._cpu_times[root]
        cpu_time = by_pid[root]["cpu_times"].user + by_pid[root]["cpu_times"].system
        for child in self._tree[root]:
            cpu_time += self._update(child, by_pid)
        self._cpu_times[root] = cpu_time
        return cpu_time

    def update(self, processes_info):
        by_pid = {}
        for pinfo in processes_info:
            pid = pinfo["pid"]
            by_pid[pid] = pinfo
            if pid not in self._known_pids:
                self._known_pids.add(pid)
                self._tree[pinfo["ppid"]].append(pid)
                self._cpu_times[pid] = 0
        self._update(self._root, by_pid)

    def fallback(self, res):
        return res.ru_utime + res.ru_stime

    def get_stats(self, pid):
        return self._cpu_times[pid]

    def should_terminate(self, pid):
        return self.get_stats(pid) > self._limit

    def get_error(self, pid):
        return (TimeoutError, "CPU time limit exceeded!")
