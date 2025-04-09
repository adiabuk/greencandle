#!/usr/bin/env bash

function usage () {
  cat << EOF
Usage: $0 [-g|-p] -f <filename> -P <port> -H <hostname>

Add and retrieve mysql db schema without data

  -g    Get schema
  -p    Put schema
  -f    filename
  -P    port
  -H    hostname
  -h    Show this message

EOF

  exit 1
}

while getopts "hgpP:H:f:" opt; do
  case $opt in
    g)
      GET=true
      ;;
    h)
      usage
      ;;
    p)
      PUT=true
      ;;
    f)
      FILENAME=$OPTARG
      DIRNAME=$(dirname $FILENAME)
      ;;
    P)
      PORT=$OPTARG
      ;;
    H)
      HOSTNAME=$OPTARG
      ;;
    \?)
      printf 'invald option\n\n'
    esac

done
[[ -z $HOSTNAME ]] && HOSTNAME=localhost
DB="greencandle"

if [[ -z $FILENAME ]]; then
  printf 'Missing filename\n\n'
  usage

elif [[ -n $GET && -n $PUT ]]; then
  printf 'Specify put or get not both\n'
  usage
elif [[ -z $GET && -z $PUT ]]; then
  printf 'Specify either put or get\n\n'
  usage

elif [[ -n $GET ]]; then
  str="show tables from $DB where Tables_in_${DB} like 'bak_%' or Tables_in_$DB like 'tmp_%';"
  TABLES=$(echo $str | mysql -N --protocol=tcp -h $HOSTNAME -P $PORT -uroot -ppassword|tr '\n' ' ')
  IGNORE_TABLES=""

  for table in `echo $TABLES`; do
    IGNORE_TABLES="$IGNORE_TABLES --ignore_table=${DB}.${table}"
  done
  [[ -z $TABLES ]] && TABLES=None
  echo "Ignoring tables: $TABLES"
  mysqldump --protocol=tcp -h $HOSTNAME -P $PORT -u root -ppassword --no-data $DB $IGNORE_TABLES --routines | sed 's/ AUTO_INCREMENT=[0-9]*//g'  > $FILENAME
  mysqldump --protocol=tcp -h $HOSTNAME -P $PORT -u root -ppassword $DB variables exchange | sed 's/ AUTO_INCREMENT=[0-9]*//g' >> $FILENAME
  sed -i 's/,)/)/g' $FILENAME

elif [[ -n $PUT ]]; then
  mysql --protocol=tcp -h $HOSTNAME -P $PORT -u root -ppassword $DB < $FILENAME
fi
echo Done
