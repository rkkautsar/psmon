#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CPU_TIME_CONSUMER=$DIR/../_gadgets/cpu_time_consumer.py

CPU_TIME_1_SCRIPT=$DIR/child_cpu_time_1.sh

$CPU_TIME_1_SCRIPT &
$CPU_TIME_CONSUMER 9 &
sleep 3

