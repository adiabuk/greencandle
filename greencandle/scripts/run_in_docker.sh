#!/usr/bin/env bash
YEAR=$1
STRATEGY=$2
PAIR=$3
base_dir=/data/$STRATEGY

if [[ -z $PAIR ]]; then
   echo "Usage: $0 <YEAR> <STRATEGY> <PAIR>"
  exit 1
fi

date=`date +"%Y-%m-%d"`

mkdir -p ${base_dir}/${YEAR}
echo $PAIR $date
backend_test -d /data/altcoin_historical/${YEAR}/year/ -s -i 4h -p $PAIR &> ${base_dir}/${YEAR}/${PAIR}_${date}.log
create_graph -d1 -p $PAIR -i 4h -o ${basedir}/${YEAR}
report ${base_dir}/${YEAR}/${PAIR}_${date}.xlsx &>> ${base_dir}/${YEAR}/${PAIR}_${date}.log
redis-dump --db=1 > ${base_dir}/${YEAR}/${PAIR}_${date}.rs
