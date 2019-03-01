import unittest
import os.path
from pathlib import Path
from psmon.main import run

DIR = os.path.dirname(os.path.realpath(__file__))


class MemoryUsageTestCase(unittest.TestCase):
    def test_memory_usage(self):
        program = Path(DIR) / "_programs" / "child_memory.sh"
        limit = 300 * 1024 * 1024
        stats = run([program], memory_limit=limit)
        self.assertLess(stats["max_memory"], 1.5 * limit)

    def test_memory_human(self):
        program = Path(DIR) / "_programs" / "child_memory.sh"
        limit = 300 * 1024 * 1024
        limit_human = "300M"
        stats = run([program], memory_limit=limit_human)
        self.assertLess(stats["max_memory"], 1.5 * limit)
