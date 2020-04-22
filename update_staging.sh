#!/usr/bin/env bash

set -e

git pull
if [[ -n "$1" ]]; then
  export TAG=$1
else
  export TAG=$(python greencandle/version.py)
fi
docker-compose -f ./install/docker-compose_stag.yml pull
base=$(yq r install/*stag* services | grep -v '^ .*' | sed 's/:.*$//'|grep -vE '\-|cron|api')
gc=$(yq r install/*stag* services | grep -v '^ .*' | sed 's/:.*$//'|grep '\-')

docker-compose -f ./install/docker-compose_stag.yml up -d $base

for i in $gc; do
  docker-compose -f ./install/docker-compose_stag.yml up -d $i
  sleep 60
done

sleep 120
docker-compose -f ./install/docker-compose_stag.yml up -d cron api

docker system prune --volumes --all -f
