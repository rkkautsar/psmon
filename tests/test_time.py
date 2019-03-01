import unittest
import os.path
from pathlib import Path
from psmon.main import run

DIR = os.path.dirname(os.path.realpath(__file__))

TOLERANCE = 0.5


class CPUTimeTestCase(unittest.TestCase):
    def test_children(self):
        program = Path(DIR) / "_programs" / "child_cpu_time_1.sh"
        limit = 3
        stats = run([program], cpu_time_limit=limit)
        self.assertLess(stats["cpu_time"], limit + TOLERANCE)

    def test_grandchildren(self):
        program = Path(DIR) / "_programs" / "child_cpu_time_2.sh"
        limit = 3
        # Need faster polling
        stats = run([program], cpu_time_limit=limit, period=0.05)
        self.assertLess(stats["cpu_time"], limit + TOLERANCE)


class WallTimeTestCase(unittest.TestCase):
    def test_children(self):
        program = Path(DIR) / "_programs" / "child_cpu_time_1.sh"
        limit = 3
        stats = run([program], wall_time_limit=limit)
        self.assertLess(stats["wall_time"], limit + TOLERANCE)

    def test_grandchildren(self):
        program = Path(DIR) / "_programs" / "child_cpu_time_2.sh"
        limit = 3
        stats = run([program], wall_time_limit=limit)
        self.assertLess(stats["wall_time"], limit + TOLERANCE)

