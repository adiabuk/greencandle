#!/usr/bin/env bash

set -e

while getopts e:v: flag
do
    case "${flag}" in
        e) env=${OPTARG};;
        v) version=${OPTARG};;
    esac
done

if [[ -z $env ]]; then
  echo "Usage $0 -e [stag|prod] -v <version>"
  exit 1
elif [[ -z $version ]]; then
  version=$(python greencandle/version.py)
fi

echo "env: $env";
echo "version: $version";

export TAG=$version
export HOSTNAME=$env
git pull
docker-compose -f ./install/docker-compose_${env}.yml pull
base=$(yq r install/*${env}* services | grep -v '^ .*' | sed 's/:.*$//'|grep 'base')
be=$(yq r install/*${env}* services | grep -v '^ .*' | sed 's/:.*$//'|grep 'be')
fe=$(yq r install/*${env}* services | grep -v '^ .*' | sed 's/:.*$//'|grep 'fe')


docker-compose -f ./install/docker-compose_${env}.yml up --remove-orphans -d $base

for container in $be; do
  docker-compose -f ./install/docker-compose_${env}.yml up -d $container
  sleep 60
done

sleep 120
docker-compose -f ./install/docker-compose_${env}.yml up -d $fe

docker system prune --volumes --all -f
