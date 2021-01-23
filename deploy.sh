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
url=$(configstore package get $env slack_notifications)
text="Starting deployment $TAG on $HOSTNAME"
curl -X POST -H 'Content-type: application/json' --data '{"text":"'"${text}"'"}' $url
git pull

# Stop existing fe and be containers
docker ps --filter name=^fe-* --filter name=^be-* -q | xargs docker stop
docker ps --filter name=^fe-* -q | xargs docker rm
docker volume prune -f

FILE=database_change.sql
if test -f "$FILE"; then
  mysql --host mysql -uroot -ppassword greencandle < $FILE
fi


docker-compose -f ./install/docker-compose_${env}.yml pull
base=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'base')
be=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'be')
fe=$(yq r install/docker-compose_${env}.yml services | grep -v '^ .*' | sed 's/:.*$//'|grep 'fe')


docker-compose -f ./install/docker-compose_${env}.yml up --remove-orphans -d $base

for container in $be; do
  docker-compose -f ./install/docker-compose_${env}.yml up -d $container
  sleep 15
done

sleep 30
docker-compose -f ./install/docker-compose_${env}.yml up -d $fe

docker system prune --volumes --all -f
text="Finished deployment $TAG on $HOSTNAME"
curl -X POST -H 'Content-type: application/json' --data '{"text":"'"${text}"'"}' $url

