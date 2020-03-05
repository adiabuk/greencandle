#!/usr/bin/env bash
YEAR=$1
strategy=$2
pair=$3
base_dir=/data/$strategy

if [[ -z $pair ]]; then
   echo "Usage: $0 <YEAR> <strategy>"
  exit 1
fi

date=`date +"%Y-%m-%d"`

mkdir -p ${base_dir}/${YEAR}
echo $pair $date
backend_test -d /data/altcoin_historical/${YEAR}/YEAR/ -s -i 4h -p $pair &> ${base_dir}/${YEAR}/${pair}_${date}.log
create_graph -d1 -p $pair -i 4h -o ${basedir}/${YEAR} &>/dev/null
report ${base_dir}/${YEAR}/${pair}_${date}.xlsx &>> ${base_dir}/${YEAR}/${pair}_${date}.log
redis-dump --db=1 > ${base_dir}/${YEAR}/${pair}_${date}.rs
aws s3 cp ${base_dir}/${YEAR}/${pair}_${date}.{rs,log,xlsx} s3://greencandle/${YEAR}/
