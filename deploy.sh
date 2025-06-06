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
  echo "Usage $0 -e <env> -v <version>"
  exit 1
elif [[ -z $version ]]; then
  version=$(python greencandle/version.py)
fi

echo "env: $env";
echo "version: $version";
export COMMIT=$(git rev-parse HEAD |cut -c1-8)
export HOST_IP=$(ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+')
export TAG=$version
export SECRET_KEY=$(hexdump -vn16 -e'4/4 "%08X" 1 "\n"' /dev/urandom)
export COMPOSE="docker compose --ansi never -f ./install/docker-compose_${env}.yml -p ${env}"

echo "$TAG,$env,$COMMIT,`date` start" >> /var/local/deploy.txt
$COMPOSE pull
base=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'base') || true

be=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'be') || true
fe=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'fe')  || true
all_be=$(docker ps | grep ${env}.*be |awk {'print $NF'}) || true
all_fe=$(docker ps | grep ${env}.*fe |awk {'print $NF'} | grep -v stream) || true

# Stop existing fe and be containers
docker stop $all_fe $all_be || true
docker rm $all_fe $all_be || true

$COMPOSE up -d $base --force-recreate
$COMPOSE up -d $fe --force-recreate
$COMPOSE up -d $be --force-recreate

export COMMIT=`docker exec ${env}-base-mysql  bash -c 'echo "$COMMIT_SHA"'`

# log tag, env short commit sha, and date to log file
echo "$TAG,$env,$COMMIT,`date` finish" >> /var/local/deploy.txt
echo DONE
