#!/usr/bin/env bash

set -e

function get_payload() {
  payload='{"text": "'${1}'", "channel": "notifications", "username": "deploy-bot",
            "content": "shit", "icon_emoji": ":rocket:", }'
  echo $payload
}


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
url=$(configstore package get $env slack_url)
text="Starting deployment $TAG on $HOSTNAME"
payload=$(get_payload "$text")
curl -X POST -H "Content-Type: application/json" -d  "$payload"  $url
git pull

# Stop existing fe and be containers
docker ps --filter name=^fe-* --filter name=^be-* -q | xargs docker stop || true
docker ps --filter name=^fe-* -q | xargs docker rm || true
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

text="Finished deployment $TAG on $HOSTNAME"
payload=$(get_payload "$text")
curl -X POST -H "Content-Type: application/json" -d  "$payload"  $url
logger -t deploy "$TAG successfully deployed"

