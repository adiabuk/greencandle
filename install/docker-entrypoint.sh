#!/usr/bin/env bash

set -e

if [[ -z $CONFIG_ENV ]]; then
  echo "CONFIG_ENV var not set, exiting..."
  exit 1
fi

if [[ ! -e /installed ]]; then
  configstore package process_templates --ignore-role --basedir /opt/config $CONFIG_ENV /opt/output
  cp /opt/output/greencandle.ini /etc/
  cp /opt/output/router-config.json /etc
  if [[ "$HOSTNAME" == *"webserver"* ]]; then
    cp /opt/output/default.conf /etc/nginx/conf.d/default.conf || true
    cp /opt/output/nginx.conf /etc/nginx/ || true
    cp /opt/output/50x.html /usr/share/nginx/html || true
    echo $(configstore package get $CONFIG_ENV base_env --basedir /opt/config) > /var/www/html/env.txt || true
    cp /opt/output/{*.html,*.css,*.js,*.jpg} /var/www/html ||true
    cp /opt/config/raw/main.css /opt/config/raw/favicon.ico /var/www/html || true
    > /etc/nginx/sites-available/default || true
  fi

  crontab /opt/output/gc-cron || true
  touch /installed
fi

mysql=$(awk -F "=" '/db_host/ {print $2}' /etc/greencandle.ini)
redis=$(awk -F "=" '/redis_host/ {print $2}' /etc/greencandle.ini)

while ! nc -z $mysql 3306; do
  echo Waiting for mysql;
  sleep 1;
done

while ! nc -z $redis 6379; do
  echo Waiting for redis;
  sleep 1;
done

exec "$@"
