from psmon.limiters.base import CommonResourceLimiter


class CpuTimeLimiter(CommonResourceLimiter):
    watched_attrs = ["cpu_times"]

    def _get_resource_usage(self, stats, pid):
        if stats["cpu_times"] is None:
            return self._resource_usage[pid]
        return stats["cpu_times"].user + stats["cpu_times"].system

    @classmethod
    def fallback(cls, res):
        return res.ru_utime + res.ru_stime

    @classmethod
    def _get_max_usage(cls, previous, current):
        return current

    @classmethod
    def get_error(cls, pid):
        return (TimeoutError, "CPU time limit exceeded!")
