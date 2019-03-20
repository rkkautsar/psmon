import os
import threading

import psutil


class FileReader(threading.Thread):
    def __init__(self, fd, queue):
        super().__init__()
        self._fd = fd
        self._queue = queue

    def run(self):
        for line in iter(self._fd.readline, b""):
            self._queue.put(line)


def extract_file_queue(queue):
    result = b""
    while not queue.empty():
        result += queue.get()
    return result


def first_true(pred, iterable, default=None):
    """Returns the first true value in the iterable.

    If no true value is found, returns *default*

    source: https://docs.python.org/3/library/itertools.html
    """
    # first_true([a,b,c], x) --> a or b or c or x
    # first_true([a,b], x, f) --> a if f(a) else b if f(b) else x
    return next(filter(pred, iterable), default)


def graceful_kill(processes, timeout=3):
    """
    Terminate then kill pids after ${timeout} s.
    Also return returncode as dict([pid]: returncode)
    """

    stopped = []
    initially_gone = [p for p in processes if not p.is_running()]
    processes = [p for p in processes if p not in initially_gone]

    for proc in processes:
        try:
            proc.terminate()
        except psutil.NoSuchProcess:
            continue

    gone, alive = psutil.wait_procs(processes, timeout=timeout)
    stopped += gone

    if len(alive) > 0:
        for proc in alive:
            proc.kill()
        gone, alive = psutil.wait_procs(processes, timeout=timeout)
        stopped += gone

    returncodes = {proc.pid: proc.returncode for proc in stopped}
    for proc in initially_gone:
        try:
            ret = os.waitpid(proc.pid, 0)
            returncodes[proc.pid] = ret
        except ChildProcessError:
            continue

    return returncodes
