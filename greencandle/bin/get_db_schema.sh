#!/usr/bin/env bash

function usage () {
  cat << EOF
Usage: $0 [-g|-p] -f <filename> -P <port>

Add and retrieve mysql db schema without data

  -g    Get schema
  -p    Put schema
  -f    filename
  -P    port
  -h    Show this message

EOF

  exit 1
}

while getopts "hgpP:f:" opt; do
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
    \?)
      printf 'invald option\n\n'
    esac

done

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
  mysqldump --protocol=tcp -P $PORT -u root -ppassword --no-data greencandle > $FILENAME
  mysqldump --protocol=tcp -P $PORT -u root -ppassword greencandle exchange >> $FILENAME
elif [[ -n $PUT ]]; then
  mysql --protocol=tcp -P $PORT -u root -ppassword greencandle < $FILENAME
fi
