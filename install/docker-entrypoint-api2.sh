#!/usr/bin/env bash

set -e

if [[ -z $CONFIG_ENV ]]; then
  echo "CONFIG_ENV var not set, exiting..."
  exit 1
fi

if [[ ! -e /installed ]]; then
  configstore package process_templates --ignore-role --basedir /opt/config $CONFIG_ENV /opt/output
  cp /opt/output/default.ap /etc/nginx/conf.d/default.conf || true
  cp /opt/output/nginx.conf /etc/nginx/ || true
  cp /opt/output/50x.html /usr/share/nginx/html || true
  echo $(configstore package get $CONFIG_ENV base_env) > /var/www/html/env.txt || true
  cp /opt/output/{*.html,*.css,*.js,*.jpg} /var/www/html ||true
  > /etc/nginx/sites-available/default || true
  touch /installed
fi

exec "$@"
