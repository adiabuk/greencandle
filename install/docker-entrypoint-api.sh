#!/usr/bin/env bash

set -e

if [[ -z $CONFIG_ENV ]]; then
  echo "CONFIG_ENV var not set, exiting..."
  exit 1
fi

while ! nc -z mysql 3306; do
  echo Waiting for mysql;
  sleep 1;
done

while ! nc -z redis 6379; do
  echo Waiting for redis;
  sleep 1;
done
if [[ ! -e /installed ]]; then
  configstore package process_templates --ignore-role --basedir /opt/config $CONFIG_ENV /opt/output
  cp /opt/output/greencandle.ini /etc/greencandle.ini || true
  mkdir /etc/gcapi
  cp /opt/config/raw/* /etc/gcapi/
  touch /installed
fi
exec "$@"
