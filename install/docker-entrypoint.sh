#!/usr/bin/env bash

set -e

if [[ -z $CONFIG_ENV ]]; then
  echo "CONFIG_ENV var not set, exiting..."
  exit 1
fi

if [[ ! -f /installed ]]; then
  declare -p | grep -Ev 'BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID' > /container.env
  configstore package process_templates --ignore-role --basedir /opt/config $CONFIG_ENV /opt/output
  cp /opt/output/greencandle.ini /opt/output/send_nsca.cfg /opt/output/router_config.json /opt/output/alert.ini /etc
  [[ ! -d /var/local/lock/ ]] && mkdir -p /var/local/lock


  if [[ "$HOSTNAME" == *"web"* ]]; then
    cp /opt/output/default.conf /etc/nginx/conf.d/default.conf
    if [[ "$HOSTNAME" == *"webserver"* ]]; then
      cp /opt/output/nginx.conf /etc/nginx/
    else
      cp /opt/output/default.ap /etc/nginx/conf.d/default.conf
    fi
    mkdir -p /var/www/html
    base_env=$(configstore package get $CONFIG_ENV base_env --basedir /opt/config)
    echo "$base_env ($VERSION)" > /var/www/html/env.txt
    cp /opt/output/{*.html,*.css,*.js,*.jpg} /var/www/html
    cp /opt/config/raw/main.css /opt/config/raw/50x.html /var/www/html
    cp /opt/config/raw/favicon-${base_env}.ico  /var/www/html/favicon.ico
    > /etc/nginx/sites-available/default

  elif [[ "$HOSTNAME" == *"api"* ]]; then
    mkdir -p /var/www/html
    base_env=$(configstore package get $CONFIG_ENV base_env --basedir /opt/config)
    echo "$base_env ($VERSION)" > /var/www/html/env.txt
    cp /opt/config/raw/main.css /opt/config/raw/50x.html /var/www/html
    cp /opt/config/raw/favicon-${base_env}.ico  /var/www/html/favicon.ico
    cp /opt/config/raw/* /var/www/html/

  elif [[ "$HOSTNAME" == *"redis"* ]]; then
    cp /opt/output/redis.conf /etc

  elif [[ "$HOSTNAME" == *"cron"* ]]; then
    crontab /opt/output/gc-cron

  elif [[ "$HOSTNAME" == *"alert"* ]]; then
    mkdir -p /srv/output
    cp /srv/alert/*.mp3 /srv/output/


  elif [[ "$HOSTNAME" == *"manual"* ]]; then
    pip install ipython
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
fi
touch /installed

bash -c "$@";
