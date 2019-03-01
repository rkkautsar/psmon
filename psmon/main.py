import os
import multiprocessing
import time
import signal
from subprocess import Popen, PIPE
from collections import namedtuple
import resource
import subprocess

import psutil

from psmon.process import ProcessNode
from psmon.utils import graceful_kill, human2bytes

WALL_EXCEEDED_STR = "Wall time limit exceeded!"
CPU_EXCEEDED_STR = "CPU time limit exceeded!"
MEMORY_EXCEEDED_STR = "Memory usage limit exceeded!"


class Watcher(multiprocessing.Process):
    def __init__(
        self,
        root_pid,
        period=0.1,
        wall_time_limit=None,
        cpu_time_limit=None,
        memory_limit=None,
        pipe=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.pipe = pipe
        self.root_pid = root_pid
        self.period = period
        self.wall_time_limit = wall_time_limit
        self.cpu_time_limit = cpu_time_limit
        self.memory_limit = memory_limit
        self.processes = {}

    def get_processes_info(self):
        return [
            p.info
            for p in psutil.process_iter(
                attrs=["pid", "ppid", "cpu_times", "memory_info", "status"]
            )
            if p.info["pid"] in self.processes or p.info["ppid"] in self.processes
        ]

    def stop_processes(self, error=None, error_str=None, timeout=3):
        if error_str:
            print("[!] {}".format(error_str))

        processes_info = self.get_processes_info()
        running_pids = [
            pinfo["pid"]
            for pinfo in processes_info
            if pinfo["status"] == psutil.STATUS_RUNNING
        ]

        graceful_kill(running_pids, [signal.SIGTERM, signal.SIGKILL], timeout)

    def run(self):
        self.processes[self.root_pid] = ProcessNode(self.root_pid)
        root_process = psutil.Process(self.root_pid)

        start_time = time.monotonic()

        if self.wall_time_limit:

            def alarm_handler(*args):
                self.stop_processes(error=TimeoutError, error_str=WALL_EXCEEDED_STR)

            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(self.wall_time_limit)

        while (
            root_process.is_running()
            and not root_process.status() == psutil.STATUS_ZOMBIE
        ):
            processes_info = self.get_processes_info()

            for pinfo in processes_info:
                if pinfo["pid"] not in self.processes:
                    self.processes[pinfo["pid"]] = ProcessNode(pinfo["pid"])
                    self.processes[pinfo["ppid"]].add_child(
                        self.processes[pinfo["pid"]]
                    )

                if pinfo["cpu_times"] is None or pinfo["memory_info"] is None:
                    continue

                cpu_time = pinfo["cpu_times"].user + pinfo["cpu_times"].system
                memory = pinfo["memory_info"].rss

                self.processes[pinfo["pid"]].update(cpu_time, memory)

            if (
                self.cpu_time_limit
                and self.processes[self.root_pid].cpu_time > self.cpu_time_limit
            ):
                self.stop_processes(error=TimeoutError, error_str=CPU_EXCEEDED_STR)
                break

            if (
                self.memory_limit
                and self.processes[self.root_pid].max_memory > self.memory_limit
            ):
                self.stop_processes(error=MemoryError, error_str=MEMORY_EXCEEDED_STR)
                break

            time.sleep(self.period)

        signal.alarm(0)
        self.stop_processes()
        self.pipe.send(
            dict(
                wall_time=time.monotonic() - start_time,
                cpu_time=self.processes[self.root_pid].cpu_time,
                max_memory=self.processes[self.root_pid].max_memory,
            )
        )


def run(
    args,
    *popenargs,
    wall_time_limit=None,
    cpu_time_limit=None,
    memory_limit=None,
    **kwargs,
):
    process = Popen(args, *popenargs, stdout=PIPE, stderr=PIPE, preexec_fn=os.setpgrp)
    process.poll()
    if type(memory_limit) == str:
        memory_limit = human2bytes(memory_limit)

    recv_pipe, send_pipe = multiprocessing.Pipe(duplex=False)
    watcher_process = Watcher(
        process.pid,
        wall_time_limit=wall_time_limit,
        cpu_time_limit=cpu_time_limit,
        memory_limit=memory_limit,
        pipe=send_pipe,
        daemon=True,
        **kwargs,
    )
    watcher_process.start()
    outs, errs = process.communicate()
    # process.wait()
    stats = recv_pipe.recv()
    print(stats)
    watcher_process.join()
    return stats
