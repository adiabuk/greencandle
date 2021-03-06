#!/usr/bin/env bash

YEAR=$1
STRATEGY=$2
INTERVAL=$3
ARGS=$4
shift 4
PAIR=${@^^}  # Ensure pair is uppercase
date=`date +"%Y-%m-%d"`

if [[ $ARGS == *"-m"* ]]; then
  month=`echo $ARGS|cut -d "m" -f2-|sed 's/ //g'`
  data="/data/altcoin_historical/${YEAR}/monthly/${month}/"
else
  data="/data/altcoin_historical/${YEAR}/year/"
fi

if [[ $ARGS == *"-a"* ]]; then
  base_dir=/data/output/parallel/$YEAR
  filename=${base_dir}/${STRATEGY}_${date}
elif [[ $ARGS == *"-m"* ]]; then
  base_dir=/data/output/${STRATEGY}/$YEAR/${month}
  filename=${base_dir}/${PAIR}_${date}
  ARGS=`echo $ARGS|cut -c 1-2`
else
  base_dir=/data/output/$STRATEGY/$YEAR
  filename=${base_dir}/${PAIR}_${date}
fi
if [[ -z $PAIR ]]; then
   echo "Usage: $0 <YEAR> <STRATEGY> <PAIR>"
  exit 1
fi


mkdir -p ${base_dir}
backend_test -d $data $ARGS -i $INTERVAL -p "$PAIR" &> ${filename}.log

if [[ $ARGS == *"-a"* ]]; then
  create_graph -a -i $INTERVAL -o $base_dir
else
  create_graph -p $PAIR -i $INTERVAL -o ${base_dir}
  create_drawdownchart $INTERVAL ${base_dir}/${PAIR}_drawdown_${date}.html
  create_drawupchart $INTERVAL ${base_dir}/${PAIR}_drawup_${date}.html
fi

report $INTERVAL ${filename}.xlsx &>> ${filename}.log
redis-dump --db=0 > ${filename}.rs
mysqldump --protocol=tcp -uroot -ppassword greencandle > ${filename}.sql
gzip ${filename}.log ${filename}.sql
