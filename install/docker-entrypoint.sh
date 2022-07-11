#!/usr/bin/env bash

set -e

if [[ -z $CONFIG_ENV ]]; then
  echo "CONFIG_ENV var not set, exiting..."
  exit 1
fi

if [[ ! -e /installed ]]; then
  configstore package process_templates --ignore-role --basedir /opt/config $CONFIG_ENV /opt/output
  cp /opt/output/greencandle.ini /opt/output/router_config.json /opt/output/alert.ini /etc

  if [[ "$HOSTNAME" == *"web"* ]]; then
    cp /opt/output/default.conf /etc/nginx/conf.d/default.conf
    if [[ "$HOSTNAME" == *"webserver"* ]]; then
      cp /opt/output/nginx.conf /etc/nginx/
    else
      cp /opt/output/default.ap /etc/nginx/conf.d/default.conf
    fi
    mkdir -p /var/www/html
    echo $(configstore package get $CONFIG_ENV base_env --basedir /opt/config) > /var/www/html/env.txt
    cp /opt/output/{*.html,*.css,*.js,*.jpg} /var/www/html
    cp /opt/config/raw/main.css /opt/config/raw/50x.html /opt/config/raw/favicon.ico /var/www/html
    > /etc/nginx/sites-available/default

  elif [[ "$HOSTNAME" == *"api"* ]]; then
    mkdir -p /etc/gcapi /var/www/html
    echo $(configstore package get $CONFIG_ENV base_env --basedir /opt/config) > /var/www/html/env.txt
    cp /opt/config/raw/* /etc/gcapi/

  elif [[ "$HOSTNAME" == *"cron"* ]]; then
    crontab /opt/output/gc-cron

  elif [[ "$HOSTNAME" == *"alert"* ]]; then
    cp /srv/alert/com.mp3 /srv/alert/250ms-silence.mp3 /

  elif [[ "$HOSTNAME" == *"manual"* ]]; then
    easy_install pip
    pip install ipython
  fi

  touch /installed

fi

if [[ $DB == true ]]; then
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
  echo "Done waiting for DB services"
fi

exec "$@"
