import os.path
import unittest
from pathlib import Path
from tempfile import TemporaryFile

from psmon import ProcessMonitor
from psmon.limiters import WallTimeLimiter
from psmon.limiters.cpu_times import CpuTimeLimiter
from psmon.limiters.max_memory import MaxMemoryLimiter

DIR = os.path.dirname(os.path.realpath(__file__))


class CoreTestCase(unittest.TestCase):
    def test_deep_sigterm_handler(self):
        program = Path(DIR) / "_programs" / "sigterm_echo.sh"
        num = 2
        monitor = ProcessMonitor(
            [program, str(num), "10"], capture_output=True, text=True
        )
        monitor.subscribe("wall_time", WallTimeLimiter(1))
        stats = monitor.run()
        num_echo = "\n".join(stats["stdout"]).count("got SIGTERM")
        self.assertEqual(num_echo, num)

    def test_fast_exit(self):
        command = ["echo", "1"]
        num = 2
        monitor = ProcessMonitor(command, capture_output=True)
        monitor.subscribe("wall_time", WallTimeLimiter(1))
        monitor.subscribe("cpu_time", CpuTimeLimiter(1))
        monitor.subscribe("max_memory", MaxMemoryLimiter(1000000))
        stats = monitor.run()
        self.assertEqual(stats["stdout"], [b"1\n"])
        self.assertEqual(stats["return_code"], 0)
        self.assertGreater(stats["wall_time"], 0)
        self.assertGreater(stats["cpu_time"], 0)
        self.assertGreater(stats["max_memory"], 0)
