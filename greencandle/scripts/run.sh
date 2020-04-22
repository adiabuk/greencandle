#!/usr/bin/env bash
year=$1
strategy=$2
base_dir=/data/$strategy
if [[ -z $strategy ]]; then
   echo "Usage: $0 <year> <strategy>"
  exit 1
fi

date=`date +"%Y-%m-%d"`

mkdir -p ${base_dir}/${year}
for pair in `cat /data/altcoin_historical/all_pairs.txt`; do
  echo $pair $date
  backend_test -d /data/altcoin_historical/${year}/year/ -s -i 4h -p $pair &> ${base_dir}/${year}/${pair}_${date}.log
  create_graph -d0 -p $pair -i 4h -o ${basedir}/${year} &>/dev/null
  report 4h ${base_dir}/${year}/${pair}_${date}.xlsx &>> ${base_dir}/${year}/${pair}_${date}.log
  redis-dump --db=0 > ${base_dir}/${year}/${pair}_${date}.rs
done
