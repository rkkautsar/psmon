from psmon.limiters.base import CommonResourceLimiter


class MaxMemoryLimiter(CommonResourceLimiter):
    watched_attrs = ["memory_info"]

    def _get_resource_usage(self, stats, pid):
        if stats["memory_info"] is None:
            return self._resource_usage[pid]
        return stats["memory_info"].rss

    @classmethod
    def fallback(cls, res):
        return res.ru_maxrss

    @classmethod
    def get_error(cls, pid):
        return (MemoryError, "Max memory limit exceeded!")
