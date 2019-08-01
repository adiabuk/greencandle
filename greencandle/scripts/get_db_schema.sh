#!/usr/bin/env bash

function usage () {
  cat << EOF
Usage: $0 [-g|-p] -f <filename>

Get and put arch packages on the system using pacman and yaourt

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
  mysqldump --protocol=tcp -u greencandle -ppassword --no-data greencandle > $FILENAME
  mysqldump --protocol=tcp -u greencandle -ppassword greencandle exchange >> $FILENAME
elif [[ -n $PUT ]]; then
  mysql --protocol=tcp -u greencandle -ppassword greencandle < $FILENAME
  mysql --protocol=tcp -u greencandle -ppassword greencandle_test < $FILENAME
fi
