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

configstore package process_templates --ignore-role --basedir /opt/config $CONFIG_ENV /opt/output
cp /opt/output/greencandle.ini /etc/greencandle.ini || true
cp /opt/output/default.conf /etc/nginx/conf.d/default.conf || true
cp /opt/output/nginx.conf /etc/nginx/ || true
echo $HOST > /var/www/html/env.txt || true
cp /opt/output/{*.html,*.css,*.js,*.jpg} /var/www/html ||true
crontab /opt/output/gc-cron || true
> /etc/nginx/sites-available/default || true

exec "$@"
