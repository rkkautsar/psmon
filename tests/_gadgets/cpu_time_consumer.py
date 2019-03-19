#!/usr/bin/env python

"""
Use 100% CPU for $(argv[1]) seconds, then sleep for $(argv[2] = 0) seconds.
"""

import sys
import time

time_to_consume = int(sys.argv[1])
start_time = time.perf_counter()

dummy = 0
while time.perf_counter() - start_time < time_to_consume:
    dummy = dummy + 1

if len(sys.argv) > 2:
    time_to_sleep = int(sys.argv[2])
    time.sleep(time_to_sleep)
