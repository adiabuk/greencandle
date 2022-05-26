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
  echo "Usage $0 -e [stag|prod|test|data] -v <version>"
  exit 1
elif [[ -z $version ]]; then
  version=$(python greencandle/version.py)
fi

echo "env: $env";
echo "version: $version";

export HOST_IP=$(ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+')
export TAG=$version
export HOSTNAME=$env

# Stop existing fe and be containers
docker ps --filter name=fe-* --filter name=be-* -q | xargs docker stop || true
docker ps --filter name=fe-* --filter name=be-* -q | xargs docker rm || true
docker volume prune -f

docker-compose -f ./install/docker-compose_${env}.yml pull
base=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'base')

be=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'be')
fe=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'fe')


docker-compose -f ./install/docker-compose_${env}.yml up --remove-orphans -d $base

for container in $be; do
  docker-compose -f ./install/docker-compose_${env}.yml up -d $container
  sleep 5
done

sleep 5
docker-compose -f ./install/docker-compose_${env}.yml up -d $fe

logger -t deploy "$TAG successfully deployed"

