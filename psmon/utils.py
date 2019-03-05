import os
import time
import psutil


def _is_running(pid):
    try:
        id, sts = os.waitpid(pid, os.WNOHANG)
        return id == pid
    except ChildProcessError:
        try:
            return psutil.Process(pid).is_running()
        except:
            return False


def graceful_kill(pids, timeout=3):
    """
    Terminate then kill pids after ${timeout} s.
    Also return returncode as dict([pid]: returncode)
    """

    stopped = []
    initially_gone = [pid for pid in pids if not psutil.pid_exists(pid)]
    alive = [pid for pid in pids if psutil.pid_exists(pid)]
    procs = [psutil.Process(pid) for pid in alive]

    for proc in procs:
        proc.terminate()

    gone, alive = psutil.wait_procs(procs, timeout=timeout)
    stopped += gone

    if len(alive) > 0:
        for proc in alive:
            proc.kill()
        gone, alive = psutil.wait_procs(procs, timeout=timeout)
        assert len(alive) > 0
        stopped += gone

    returncodes = {proc.pid: proc.returncode for proc in stopped}
    for pid in initially_gone:
        try:
            ret = os.waitpid(pid, 0)
            returncodes[pid] = ret
        except:
            continue

    return returncodes


## {{{ http://code.activestate.com/recipes/578019/ (r15)
"""
Bytes-to-human / human-to-bytes converter.
Based on: http://goo.gl/kTQMs
Working with Python 2.x and 3.x.
Author: Giampaolo Rodola' <g.rodola [AT] gmail [DOT] com>
License: MIT
"""

# see: http://goo.gl/kTQMs
SYMBOLS = {
    "customary": ("B", "K", "M", "G", "T", "P", "E", "Z", "Y"),
    "customary_ext": (
        "byte",
        "kilo",
        "mega",
        "giga",
        "tera",
        "peta",
        "exa",
        "zetta",
        "iotta",
    ),
    "iec": ("Bi", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi"),
    "iec_ext": ("byte", "kibi", "mebi", "gibi", "tebi", "pebi", "exbi", "zebi", "yobi"),
}


def human2bytes(s):
    """
    Attempts to guess the string format based on default symbols
    set and return the corresponding bytes as an integer.
    When unable to recognize the format ValueError is raised.
      >>> human2bytes('0 B')
      0
      >>> human2bytes('1 K')
      1024
      >>> human2bytes('1 M')
      1048576
      >>> human2bytes('1 Gi')
      1073741824
      >>> human2bytes('1 tera')
      1099511627776
      >>> human2bytes('0.5kilo')
      512
      >>> human2bytes('0.1  byte')
      0
      >>> human2bytes('1 k')  # k is an alias for K
      1024
      >>> human2bytes('12 foo')
      Traceback (most recent call last):
          ...
      ValueError: can't interpret '12 foo'
    """
    init = s
    num = ""
    while s and s[0:1].isdigit() or s[0:1] == ".":
        num += s[0]
        s = s[1:]
    num = float(num)
    letter = s.strip()
    for name, sset in SYMBOLS.items():
        if letter in sset:
            break
    else:
        if letter == "k":
            # treat 'k' as an alias for 'K' as per: http://goo.gl/kTQMs
            sset = SYMBOLS["customary"]
            letter = letter.upper()
        else:
            raise ValueError("can't interpret %r" % init)
    prefix = {sset[0]: 1}
    for i, s in enumerate(sset[1:]):
        prefix[s] = 1 << (i + 1) * 10
    return int(num * prefix[letter])


## end of http://code.activestate.com/recipes/578019/ }}}
