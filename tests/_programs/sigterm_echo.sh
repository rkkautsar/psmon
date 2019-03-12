#!/bin/bash

trap "echo [$1] got SIGTERM; exit" SIGTERM

depth=$1

if [ $(($depth - 1)) -gt 0 ]
then
    $0 $(($depth - 1)) 30&
fi

sleep $2
