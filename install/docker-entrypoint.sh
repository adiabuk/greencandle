#!/usr/bin/env bash

set -e

if [[ -z $CONFIG_ENV ]]; then
  echo "CONFIG_ENV var not set, exiting..."
  exit 1
fi

if [[ ! -e /installed ]]; then
  configstore package process_templates --ignore-role --basedir /opt/config $CONFIG_ENV /opt/output
  cp /opt/output/greencandle.ini /etc/greencandle.ini || true
  if [[ "$HOSTNAME" == *"webserver"* ]]; then
    cp /opt/output/default.conf /etc/nginx/conf.d/default.conf || true
    cp /opt/output/nginx.conf /etc/nginx/ || true
    cp /opt/output/50x.html /usr/share/nginx/html || true
    echo $HOST > /var/www/html/env.txt || true
    cp /opt/output/{*.html,*.css,*.js,*.jpg} /var/www/html ||true
    cp /opt/config/raw/main.css /var/www/html || true
    > /etc/nginx/sites-available/default || true
  fi

  crontab /opt/output/gc-cron || true
  if [[ "$HOSTNAME" == *"router"* ]]; then
    if [[ "$CONFIG_ENV" == *"stag"* ]]; then
      cp /opt/output/router_config_stag.json /etc/router_config.json
    elif [[ "$CONFIG_ENV" == *"prod"* ]]; then
      cp /opt/output/router_config_prod.json /etc/router_config.json
    fi
  fi
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
