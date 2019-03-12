import os
import time
import atexit
import resource
import threading
import psutil
from queue import Queue
from subprocess import Popen, PIPE
from loguru import logger

from psmon.utils import graceful_kill


class Reader(threading.Thread):
    def __init__(self, fd, queue, text=False):
        super().__init__()
        self._fd = fd
        self._queue = queue
        self._text = text

    def run(self):
        for line in iter(self._fd.readline, b""):
            if self._text:
                line = line.decode().strip()
            self._queue.put(line)


class ProcessMonitor:
    def __init__(
        self,
        *popenargs,
        input=None,
        capture_output=False,
        freq=10,
        text=False,
        **kwargs,
    ):
        if input is not None:
            if "stdin" in kwargs:
                raise ValueError("stdin and input arguments may not both be used.")
            kwargs["stdin"] = PIPE

        if capture_output:
            if ("stdout" in kwargs) or ("stderr" in kwargs):
                raise ValueError(
                    "stdout and stderr arguments may not be used "
                    "with capture_output."
                )
            kwargs["stdout"] = PIPE
            kwargs["stderr"] = PIPE
            self.stdout_queue = Queue()
            self.stderr_queue = Queue()

        self.popenargs = popenargs
        self.input = input
        self.capture_output = capture_output
        self.text = text
        self.freq = freq
        self.kwargs = kwargs
        self.watchers = {}
        self.watched_attrs = dict(pid=1, ppid=1)
        self.root_process = None
        self.processes = set()

    def subscribe(self, watcher_id, watcher):
        self.watchers[watcher_id] = watcher
        for attr in watcher.watched_attrs:
            self.watch_attr(attr)

    def unsubscribe(self, watcher_id):
        watcher = self.watchers[watcher_id]
        for attr in watcher.watched_attrs:
            self.unwatch_attr(attr)
        del self.watchers[watcher_id]

    def watch_attr(self, attr):
        if attr in self.watched_attrs:
            self.watched_attrs[attr] += 1
        else:
            self.watched_attrs[attr] = 1

    def unwatch_attr(self, attr):
        self.watched_attrs[attr] -= 1
        if self.watched_attrs[attr] == 0:
            del self.watched_attrs[attr]

    def update_tree(self):
        children = self.root_process.children(recursive=True)
        self.processes.update(set(children))

    def try_get_process_info(self, process):
        try:
            return process.as_dict(list(self.watched_attrs.keys()))
        except psutil.NoSuchProcess:
            return None

    def get_processes_info(self):
        return list(
            filter(None.__ne__, [self.try_get_process_info(p) for p in self.processes])
        )

    def send_processes_stats(self, stats):
        for watcher in self.watchers.values():
            watcher.update(stats)

    def is_root_process_running(self):
        return (
            self.root_process.is_running
            and not self.root_process.status() == psutil.STATUS_ZOMBIE
        )

    def stop(self):
        return graceful_kill(self.processes)

    def run(self):
        atexit.register(self.stop)

        stdout_reader = None
        stderr_reader = None

        with Popen(*self.popenargs, preexec_fn=os.setpgrp, **self.kwargs) as process:
            if self.capture_output:
                stdout_reader = Reader(process.stdout, self.stdout_queue, self.text)
                stderr_reader = Reader(process.stderr, self.stderr_queue, self.text)
                stdout_reader.start()
                stderr_reader.start()
            if self.input:
                process.stdin.write(self.input)

            error = None
            error_str = None
            is_premature_stop = False
            root_pid = process.pid
            for watcher in self.watchers.values():
                watcher.register_root(root_pid)
            self.root_process = psutil.Process(root_pid)
            self.processes.add(self.root_process)
            processes_info = self.get_processes_info()
            if len(processes_info) == 0:
                is_premature_stop = True
            else:
                self.send_processes_stats(processes_info)

            should_terminate = False
            while self.is_root_process_running() and not should_terminate:
                try:
                    self.update_tree()
                except psutil.NoSuchProcess:
                    break

                self.send_processes_stats(self.get_processes_info())

                for watcher in self.watchers.values():
                    if watcher.should_terminate(root_pid):
                        error, error_str = watcher.get_error(root_pid)
                        should_terminate = True
                        break

                time.sleep(1.0 / self.freq)

            if is_premature_stop:
                pid, ret, res = os.wait4(root_pid, os.WNOHANG | os.WUNTRACED)
                assert pid == root_pid
                stats = {
                    watcher_id: watcher.fallback(res)
                    for watcher_id, watcher in self.watchers.items()
                }
                stats["return_code"] = ret
            else:
                stats = {
                    watcher_id: watcher.get_stats(root_pid)
                    for watcher_id, watcher in self.watchers.items()
                }
                return_codes = self.stop()
                stats["return_code"] = return_codes[root_pid]

            stats["error"] = error
            stats["error_str"] = error_str

        if self.capture_output:
            stdout_reader.join()
            stderr_reader.join()
            stdout = []
            while not self.stdout_queue.empty():
                stdout.append(self.stdout_queue.get())
            stderr = []
            while not self.stderr_queue.empty():
                stderr.append(self.stderr_queue.get())
            stats["stdout"] = stdout
            stats["stderr"] = stderr

        if stats["error"]:
            logger.warning(stats["error_str"])

        atexit.unregister(self.stop)
        res = resource.getrusage(resource.RUSAGE_SELF)
        logger.info(
            f"Used approximately {res.ru_utime + res.ru_stime: .2f}s cpu time for monitoring"
        )
        return stats
