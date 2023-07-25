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
export VPN_IP=$(ip -4 addr show tun0 | grep -Po 'inet \K[\d.]+'|| echo localhost)
export SECRET_KEY=$(hexdump -vn16 -e'4/4 "%08X" 1 "\n"' /dev/urandom)
export COMPOSE="docker compose --ansi never -f ./install/docker-compose_${env}.yml -p ${env}"

$COMPOSE pull
base=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'base')

be=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'be')
fe=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'fe')
all_be=$(docker ps | grep $env |awk {'print $NF'}|grep ${env}.*be) || true
all_fe=$(docker ps | grep $env |awk {'print $NF'}|grep ${env}.*fe) || true

# Stop existing fe and be containers
docker stop $all_fe $all_be || true
docker rm $all_fe $all_be || true

$COMPOSE up -d $base
$COMPOSE up -d $fe

for container in $be; do
  $COMPOSE up -d $container
  sleep 2
  if [[ "$container" == *"get"* ]]; then
    sleep 5
  fi

done

export COMMIT=`docker exec ${env}-base-mysql  bash -c 'echo "$COMMIT_SHA"'`

# log tag, env short commit sha, and date to log file
echo "$TAG,$env,$COMMIT,`date`" >> /var/local/deploy.txt
echo DONE
