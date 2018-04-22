#!/usr/bin/env bash

for interval in 1m 3m 5m 15m; do
  printf "$interval "
  grep AMROX4 serial_240418.log |grep " $interval"|awk {'print $5'}|sort|awk -F\( {'print $2'}|awk -F, {'print $1'}|awk '{s+=$1} END {print s}'
done
