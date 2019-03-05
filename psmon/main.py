import os
import multiprocessing
import time
import signal
import resource
from subprocess import Popen, PIPE
from loguru import logger
from collections import namedtuple
import subprocess

import psutil

from psmon.process import ProcessNode
from psmon.utils import graceful_kill, human2bytes

WALL_EXCEEDED_STR = "Wall time limit exceeded!"
CPU_EXCEEDED_STR = "CPU time limit exceeded!"
MEMORY_EXCEEDED_STR = "Memory usage limit exceeded!"


def get_processes_info(processes):
    return [
        p.info
        for p in psutil.process_iter(
            attrs=["pid", "ppid", "cpu_times", "memory_info", "status"]
        )
        if p.info["pid"] in processes or p.info["ppid"] in processes
    ]


def set_limits(wall_time, cpu_time, memory, output):
    def fn():
        os.setpgrp()
        MB = 1024 * 1024
        resource.setrlimit(resource.RLIMIT_NPROC, (1024, 1024))
        if memory:
            resource.setrlimit(resource.RLIMIT_AS, (memory, memory + 100 * MB))
        if output:
            resource.setrlimit(resource.RLIMIT_FSIZE, (output, output + 100 * MB))

    return fn


def run(
    args,
    *popenargs,
    wall_time_limit=None,
    cpu_time_limit=None,
    memory_limit=None,
    output_limit=None,
    stdout=PIPE,
    stderr=PIPE,
    freq=10,
    **kwargs,
):
    if type(memory_limit) == str:
        memory_limit = human2bytes(memory_limit)

    processes = {}
    error = None
    error_str = None

    start_time = time.monotonic()

    with Popen(
        args,
        *popenargs,
        stdout=stdout,
        stderr=stdout,
        preexec_fn=set_limits(
            wall_time_limit, cpu_time_limit, memory_limit, output_limit
        ),
        **kwargs,
    ) as p:
        root_pid = p.pid

        pid, ret, res = os.wait4(root_pid, os.WNOHANG | os.WUNTRACED)
        if pid == root_pid:
            # Already terminated
            return dict(
                wall_time=time.monotonic() - start_time,
                cpu_time=res.ru_utime + res.ru_stime,
                max_memory=res.ru_maxrss,
                return_code=ret,
            )

        root_process = psutil.Process(root_pid)
        pinfo = root_process.as_dict(attrs=["cpu_times", "memory_info"])
        processes[root_pid] = ProcessNode(root_pid)

        cpu_time = 0
        memory = 0
        if pinfo["cpu_times"] is not None:
            cpu_time = pinfo["cpu_times"].user + pinfo["cpu_times"].system
        if pinfo["memory_info"] is not None:
            memory = pinfo["memory_info"].rss
        processes[root_pid].update(cpu_time, memory)

        while (
            root_process.is_running()
            and not root_process.status() == psutil.STATUS_ZOMBIE
        ):
            processes_info = get_processes_info(processes)

            for pinfo in processes_info:
                if pinfo["pid"] not in processes:
                    processes[pinfo["pid"]] = ProcessNode(pinfo["pid"])
                    processes[pinfo["ppid"]].add_child(processes[pinfo["pid"]])

                if pinfo["cpu_times"] is None or pinfo["memory_info"] is None:
                    continue

                cpu_time = pinfo["cpu_times"].user + pinfo["cpu_times"].system
                memory = pinfo["memory_info"].rss

                processes[pinfo["pid"]].update(cpu_time, memory)

            root_process_stats = processes[root_pid].get_accumulated_stats()

            if wall_time_limit and time.monotonic() - start_time > wall_time_limit:
                error = TimeoutError
                error_str = WALL_EXCEEDED_STR
                break

            if cpu_time_limit and root_process_stats["cpu_time"] > cpu_time_limit:
                error = TimeoutError
                error_str = CPU_EXCEEDED_STR
                break

            if memory_limit and root_process_stats["max_memory"] > memory_limit:
                error = MemoryError
                error_str = MEMORY_EXCEEDED_STR
                break

            time.sleep(1.0 / freq)

        end_time = time.monotonic() - start_time
        root_process_stats = processes[root_pid].get_accumulated_stats()
        stats = dict(
            wall_time=end_time,
            cpu_time=root_process_stats["cpu_time"],
            max_memory=root_process_stats["max_memory"],
            error_str=None,
            error=None,
            status_code=None,
        )

        if error:
            stats["error"] = error
            stats["error_str"] = error_str

        return_codes = graceful_kill(processes)
        stats["return_code"] = return_codes[root_pid]

    if stats["error_str"]:
        logger.warning(error_str)

    return stats
