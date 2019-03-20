#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
MEMORY_CONSUMER=$DIR/../_gadgets/memory_consumer.py

$MEMORY_CONSUMER 100 1 && echo 1 # 100 MB
$MEMORY_CONSUMER 400 1 && echo 2 # 400 MB
$MEMORY_CONSUMER 900 1 && echo 3 # 900 MB
