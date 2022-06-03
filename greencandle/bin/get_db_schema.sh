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
  mysqldump --column-statistics=0 --protocol=tcp -h $HOSTNAME -P $PORT -u root -ppassword --no-data greencandle > $FILENAME
  mysqldump --column-statistics=0 --protocol=tcp -h $HOSTNAME -P $PORT -u root -ppassword greencandle exchange >> $FILENAME
  sed -i 's/,)/)/g' $FILENAME

elif [[ -n $PUT ]]; then
  mysql --protocol=tcp -h $HOSTNAME -P $PORT -u root -ppassword greencandle < $FILENAME
fi
