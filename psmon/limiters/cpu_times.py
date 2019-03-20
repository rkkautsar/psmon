from psmon.limiters.base import CommonResourceLimiter


class CpuTimeLimiter(CommonResourceLimiter):
    watched_attrs = ["cpu_times"]

    def _get_resource_usage(self, stats, pid):
        if stats["cpu_times"] is None:
            return self._resource_usage[pid]
        return stats["cpu_times"].user + stats["cpu_times"].system

    def _get_max_usage(self, previous, current):
        return current

    def fallback(self, res):
        return res.ru_utime + res.ru_stime

    def get_error(self, pid):
        return (TimeoutError, "CPU time limit exceeded!")
