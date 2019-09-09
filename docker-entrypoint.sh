#!/usr/bin/env bash

set -e

if [[ -z $CONFIG_ENV ]]; then
  echo "CONFIG_ENV var not set, exiting..."
  exit 1
fi

configstore package process_templates --ignore-role --basedir /opt/config $CONFIG_ENV /opt/output
cp /opt/output/greencandle.ini /etc/greencandle.ini

backend -t
