#!/usr/bin/env bash
date=`date +"%Y-%m-%d"`
for pair in `cat /data/altcoin_historical/all_pairs.txt|grep NPXSETH -A2000`; do
  echo $pair $date
  backend_test -d /data/altcoin_historical/2019/year/ -s -i 4h -p $pair &> /data/2019/${pair}_${date}.log
  create_graph -d1 -p $pair -i 4h -o /data/2019 &>/dev/null
  report /data/2019/${pair}_${date}.xlsx &>> /data/2019/${pair}_${date}.log
done
