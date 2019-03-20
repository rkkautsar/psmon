#!/usr/bin/env python

"""
Use $(argv[1]) megabytes of memory, then sleep for $(argv[2] = 0) seconds.
"""

import sys
import time

mb_to_consume = int(sys.argv[1])

dummy = []

CHUNK_SIZE = 1024 * 1024
for i in range(mb_to_consume):
    dummy.append(bytearray(CHUNK_SIZE))

if len(sys.argv) > 2:
    time_to_sleep = int(sys.argv[2])
    time.sleep(time_to_sleep)
