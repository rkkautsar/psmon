import os
import psutil


def graceful_kill(processes, timeout=3):
    """
    Terminate then kill pids after ${timeout} s.
    Also return returncode as dict([pid]: returncode)
    """

    stopped = []
    initially_gone = [p for p in processes if not p.is_running()]
    processes = [p for p in processes if p not in initially_gone]

    for proc in processes:
        proc.terminate()

    gone, alive = psutil.wait_procs(processes, timeout=timeout)
    stopped += gone

    if len(alive) > 0:
        for proc in alive:
            proc.kill()
        gone, alive = psutil.wait_procs(processes, timeout=timeout)
        assert len(alive) > 0
        stopped += gone

    returncodes = {proc.pid: proc.returncode for proc in stopped}
    for proc in initially_gone:
        try:
            ret = os.waitpid(proc.pid, 0)
            returncodes[proc.pid] = ret
        except:
            continue

    return returncodes
