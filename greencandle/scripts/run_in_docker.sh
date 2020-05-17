#!/usr/bin/env bash

YEAR=$1
STRATEGY=$2
PAIR=${3^^}  # Ensure pair is uppercase
INTERVAL=$4
base_dir=/data/$STRATEGY/year


if [[ -z $PAIR ]]; then
   echo "Usage: $0 <YEAR> <STRATEGY> <PAIR>"
  exit 1
fi

date=`date +"%Y-%m-%d"`

mkdir -p ${base_dir}
echo $PAIR $date
backend_test -d /data/altcoin_historical/${YEAR}/year/ -s -i $INTERVAL -p $PAIR &> ${base_dir}/${PAIR}_${date}.log
create_graph -d0 -p $PAIR -i $INTERVAL -o ${base_dir}
create_drawdownchart $INTERVAL ${base_dir}/drawdown_${PAIR}_${date}.html
report $INTERVAL ${base_dir}/${PAIR}_${date}.xlsx &>> ${base_dir}/${PAIR}_${date}.log
redis-dump --db=0 > ${base_dir}/${PAIR}_${date}.rs
mysqldump --protocol=tcp -uroot -ppassword greencandle > ${base_dir}/${PAIR}_${date}.sql
gzip ${base_dir}/${PAIR}_${date}.sql ${base_dir}/${PAIR}_${date}.log
