#!/usr/bin/env bash

function usage () {
  cat << EOF
Usage: $0 [-g|-p] -f <filename>

Add and retrieve mysql db schema without data

  -g    Get schema
  -p    Put schema
  -f    filename
  -h    Show this message

EOF

  exit 1
}

while getopts "hgpf:" opt; do
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
  mysqldump --protocol=tcp -u root -ppassword --no-data greencandle > $FILENAME
  mysqldump --protocol=tcp -u root -ppassword greencandle exchange >> $FILENAME
elif [[ -n $PUT ]]; then
  mysql --protocol=tcp -u root -ppassword greencandle < $FILENAME
fi
