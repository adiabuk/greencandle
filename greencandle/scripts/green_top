#!/usr/bin/env bash

interval=$1

if [[ -z $interval ]]; then
  echo "Usage: $0 <interval>"
  exit 1
fi

watch -cpd "get_mysql_status $interval test 2>&1 |grep -v INFO |grep -v DEBUG |column -t -c20;
            echo -e '\n\n\n\n';
            get_recent_profit $interval test 2>&1|grep -v INFO|tail -3"

