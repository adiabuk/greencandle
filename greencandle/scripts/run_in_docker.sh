#!/usr/bin/env bash
YEAR=$1
STRATEGY=$2
PAIR=${3^^}  # Ensure pair is uppercase
INTERVAL=$4
base_dir=/data/$STRATEGY


if [[ -z $PAIR ]]; then
   echo "Usage: $0 <YEAR> <STRATEGY> <PAIR>"
  exit 1
fi

date=`date +"%Y-%m-%d"`

mkdir -p ${base_dir}/${YEAR}
echo $PAIR $date
backend_test -d /data/altcoin_historical/${YEAR}/year/ -s -i $INTERVAL -p $PAIR &> ${base_dir}/${YEAR}/${PAIR}_${date}.log
create_graph -d1 -p $PAIR -i $INTERVAL -o ${base_dir}/${YEAR}
report ${base_dir}/${YEAR}/${PAIR}_${date}.xlsx &>> ${base_dir}/${YEAR}/${PAIR}_${date}.log
redis-dump --db=1 > ${base_dir}/${YEAR}/${PAIR}_${date}.rs
mysqldump --protocol=tcp -uroot -ppassword greencandle > ${base_dir}/${YEAR}/${PAIR}_${date}.sql
gzip ${base_dir}/${YEAR}/${PAIR}_${date}.sql ${base_dir}/${YEAR}/${PAIR}_${date}.log
