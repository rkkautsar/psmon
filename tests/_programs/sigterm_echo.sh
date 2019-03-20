#!/bin/bash

trap "echo [$1] got signal SIGTERM; exit" TERM
trap "echo [$1] got signal SIGEXIT; exit" EXIT

depth=$1

if [ $(($depth - 1)) -gt 0 ]
then
    $0 $(($depth - 1)) 30&
fi

sleep $2
