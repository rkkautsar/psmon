#!/usr/bin/env python

"""
Idle for $(sys.argv[1]) seconds but ignores sigterm
"""

import sys
import signal
import time


def handler(*args, **kwargs):
    pass


signal.signal(signal.SIGTERM, handler)

ttl = int(sys.argv[1])
time.sleep(ttl)
