#!/usr/bin/env bash

# Healthcheck for API containers
# Need 2 procs running: backend_api-api.* and rq*

count=$(ps -eocommand|grep -E 'backend_api-api|^rq'|grep -v grep|wc -l)

if [[ "$count" < 2 ]]; then
    echo "not enough procs: $count"
    exit 1
elif [[ "$count" > 2 ]]; then
    echo "too many procs: $count"
    exit 1
elif [[ "$count" == 2 ]]; then
    echo "OK: $count"
    exit 0
else
    echo "unknown: $count"
    echo 3
fi
