import unittest
import os.path
from pathlib import Path
from psmon import ProcessMonitor
from psmon.limiters import MaxMemoryLimiter

DIR = os.path.dirname(os.path.realpath(__file__))


class MemoryUsageTestCase(unittest.TestCase):
    def test_memory_usage(self):
        program = Path(DIR) / "_programs" / "child_memory.sh"
        limit = 300 * 1024 * 1024
        monitor = ProcessMonitor([program])
        monitor.subscribe("max_memory", MaxMemoryLimiter(limit))
        stats = monitor.run()
        self.assertLess(stats["max_memory"], 1.5 * limit)

