#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CPU_TIME_CONSUMER=$DIR/../_gadgets/cpu_time_consumer.py
MEMORY_CONSUMER=$DIR/../_gadgets/memory_consumer.py
SURVIVING_SIGTERM=$DIR/../_gadgets/surviving_sigterm.py

$MEMORY_CONSUMER 100 1 && echo 1 # 100 MB
$MEMORY_CONSUMER 400 1 && echo 2 # 400 MB
$MEMORY_CONSUMER 900 1 && echo 3 # 900 MB
