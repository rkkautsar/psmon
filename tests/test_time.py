import unittest
import os.path
from pathlib import Path
from psmon import ProcessMonitor
from psmon.limiters import WallTimeLimiter, CpuTimeLimiter

DIR = os.path.dirname(os.path.realpath(__file__))

TOLERANCE = 0.5


class CPUTimeTestCase(unittest.TestCase):
    def test_children(self):
        program = Path(DIR) / "_programs" / "child_cpu_time_1.sh"
        limit = 2
        monitor = ProcessMonitor([program])
        monitor.subscribe("cpu_time", CpuTimeLimiter(limit))
        stats = monitor.run()
        self.assertLess(stats["cpu_time"], limit + TOLERANCE)

    def test_grandchildren(self):
        program = Path(DIR) / "_programs" / "child_cpu_time_2.sh"
        limit = 2
        monitor = ProcessMonitor([program])
        monitor.subscribe("cpu_time", CpuTimeLimiter(limit))
        stats = monitor.run()
        self.assertLess(stats["cpu_time"], limit + TOLERANCE)


class WallTimeTestCase(unittest.TestCase):
    def test_children(self):
        program = Path(DIR) / "_programs" / "child_cpu_time_1.sh"
        limit = 2
        monitor = ProcessMonitor([program])
        monitor.subscribe("wall_time", WallTimeLimiter(limit))
        stats = monitor.run()
        self.assertLess(stats["wall_time"], limit + TOLERANCE)

    def test_grandchildren(self):
        program = Path(DIR) / "_programs" / "child_cpu_time_2.sh"
        limit = 2
        monitor = ProcessMonitor([program])
        monitor.subscribe("wall_time", WallTimeLimiter(limit))
        stats = monitor.run()
        self.assertLess(stats["wall_time"], limit + TOLERANCE)

