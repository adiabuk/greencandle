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
  echo $(configstore package get $CONFIG_ENV base_env) > /var/www/html/env.txt || true
  cp /opt/config/raw/* /etc/gcapi/
  if [[ "$CONFIG_ENV" == *"stag"* ]]; then
    cp /opt/output/router_config_stag.json /etc/router_config.json
  elif [[ "$CONFIG_ENV" == *"prod"* ]]; then
    cp /opt/output/router_config_prod.json /etc/router_config.json
  elif [[ "$CONFIG_ENV" == *"per"* ]]; then
    cp /opt/output/router_config_per.json /etc/router_config.json
  fi

  touch /installed
fi
exec "$@"
