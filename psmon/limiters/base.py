from collections import defaultdict
from psmon.base import Watcher


class CommonResourceLimiter(Watcher):
    watched_attrs = []

    def __init__(self, limit=None):
        self._limit = limit
        self._known_pids = set()
        self._root = None
        self._tree = defaultdict(list)
        self._resource_usage = {}

    def register_root(self, pid):
        self._root = pid
        self._resource_usage[pid] = None

    def _get_resource_usage(self, stats, pid):
        raise NotImplementedError()

    def _update(self, root, by_pid):
        if root not in by_pid:
            return self._resource_usage[root]

        resource = self._get_resource_usage(by_pid[root], root)
        for child in self._tree[root]:
            resource += self._update(child, by_pid)

        self._resource_usage[root] = self._get_max_usage(
            self._resource_usage[root], resource
        )

        return self._resource_usage[root]

    def update(self, processes_info):
        by_pid = {}
        for pinfo in processes_info:
            pid = pinfo["pid"]
            by_pid[pid] = pinfo
            if pid not in self._known_pids:
                self._known_pids.add(pid)
                self._tree[pinfo["ppid"]].append(pid)
                self._resource_usage[pid] = None
        self._update(self._root, by_pid)

    def get_stats(self, pid):
        return self._resource_usage[pid]

    def should_terminate(self, pid):
        if not self._limit:
            return False
        return self.get_stats(pid) > self._limit

    @classmethod
    def fallback(cls, res):
        raise NotImplementedError()

    @classmethod
    def _get_max_usage(cls, previous, current):
        if previous is None:
            return current
        return max(previous, current)

    @classmethod
    def get_error(cls, pid):
        return (ResourceWarning, "Resource usage limit exceeded!")
