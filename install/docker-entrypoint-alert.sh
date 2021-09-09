#!/usr/bin/env bash

set -e

if [[ -z $CONFIG_ENV ]]; then
  echo "CONFIG_ENV var not set, exiting..."
  exit 1
fi

if [[ ! -e /installed ]]; then
  configstore package process_templates --ignore-role --basedir /opt/config $CONFIG_ENV /opt/output
  cp /opt/output/alert.ini /etc/alert.ini
  cp /srv/greencandle/alert/com.mp3 /
  touch /installed
fi
exec python /srv/greencandle/alert/webhook.py
