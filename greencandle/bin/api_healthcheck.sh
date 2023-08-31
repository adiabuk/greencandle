#!/usr/bin/env bash

# Healthcheck for API containers
# Need 2 procs running: backend_api-api.* and rq*

count=$(ps -eocommand|grep -E 'backend_api-api|^rq'|grep -v grep|wc -l)
api_health=$(curl -Isf 127.1:20000/healthcheck &>/dev/null; echo $?)
if [[ "$api_health" != 0 ]]; then
    echo "failing healthcheck curl"
    exit 1
elif [[ "$count" < 2 ]]; then
    echo "not enough procs: $count"
    exit 1
elif [[ "$count" > 2 ]]; then
    echo "too many procs: $count"
    exit 0  # don't fail due to rq fork
elif [[ "$count" == 2 ]]; then
    echo "OK: $count"
    exit 0
else
    echo "unknown: $count"
    echo 3
fi
