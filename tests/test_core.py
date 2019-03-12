import unittest
import os.path
from tempfile import TemporaryFile
from pathlib import Path
from psmon import ProcessMonitor
from psmon.limiters import WallTimeLimiter

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
