#!/usr/bin/env python

"""
Use $(argv[1]) bytes of memory, then sleep for $(argv[2] = 0) seconds.
"""

import sys
import time

bytes_to_consume = int(sys.argv[1])

dummy = "A" * bytes_to_consume

if len(sys.argv) > 2:
    time_to_sleep = int(sys.argv[2])
    time.sleep(time_to_sleep)
