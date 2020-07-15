#!/usr/bin/env bash

set -e

git pull
if [[ -n "$1" ]]; then
  export TAG=$1
else
  export TAG=$(python greencandle/version.py)
fi
docker-compose -f ./install/docker-compose_stag.yml pull
base=$(yq r install/*stag* services | grep -v '^ .*' | sed 's/:.*$//'|grep 'base')
be=$(yq r install/*stag* services | grep -v '^ .*' | sed 's/:.*$//'|grep 'be')
fe=$(yq r install/*stag* services | grep -v '^ .*' | sed 's/:.*$//'|grep 'fe')


docker-compose -f ./install/docker-compose_stag.yml up --remove-orphans -d $base

for container in $be; do
  docker-compose -f ./install/docker-compose_stag.yml up -d $container
  sleep 60
done

sleep 120
docker-compose -f ./install/docker-compose_stag.yml up -d $fe

docker system prune --volumes --all -f
