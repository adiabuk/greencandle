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
  echo "Usage $0 -e [stag|prod|per|test|data] -v <version>"
  exit 1
elif [[ -z $version ]]; then
  version=$(python greencandle/version.py)
fi

echo "env: $env";
echo "version: $version";

export HOST_IP=$(ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+')
export TAG=$version
export HOSTNAME=$env
export VPN_IP=$(ip -4 addr show tun0 | grep -Po 'inet \K[\d.]+')
export SECRET_KEY=$(hexdump -vn16 -e'4/4 "%08X" 1 "\n"' /dev/urandom)

docker compose -f ./install/docker-compose_${env}.yml pull
base=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'base')

be=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'be')
fe=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'fe')
all_be=$(docker ps | grep test|awk {'print $NF'}|grep ${env}.*be)
all_fe=$(docker ps | grep test|awk {'print $NF'}|grep ${env}.*fe)

# Stop existing fe and be containers
docker stop $all_fe $all_be || true
docker rm $all_fe $all_be || true

docker compose -f ./install/docker-compose_${env}.yml up -d $base

for container in $be; do
  docker compose -f ./install/docker-compose_${env}.yml up -d $container
  sleep 5
done

docker compose -f ./install/docker-compose_${env}.yml up -d $fe

export COMMIT=`docker exec ${env}-fe-cron  bash -c 'echo "$COMMIT_SHA"'`

# log tag, env short commit sha, and date to log file
echo "$TAG,$env,$COMMIT,`date`" > /var/local/${env}_deploy.txt

