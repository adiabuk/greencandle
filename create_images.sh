#!/usr/bin/env bash

set -e

if [[ -z $TRAVIS_BRANCH ]]; then
  TAG="latest"
elif [[ $TRAVIS_BRANCH == "master" ]]; then
  TAG="latest";
else
  TAG="release-${TRAVIS_BRANCH}"
fi

# TODO: delete dashboard image? (ds)
docker build -f install/Dockerfile-gc . -t amrox/greencandle:${TAG}
docker build -f install/Dockerfile-ms . -t amrox/gc-mysql:${TAG}
docker build -f install/Dockerfile-rs . -t amrox/gc-redis:${TAG}
docker build -f install/Dockerfile-wb . -t amrox/webserver:${TAG}
docker build -f install/Dockerfile-as . -t amrox/alert:${TAG}

docker push amrox/greencandle:${TAG}
docker push amrox/gc-mysql:${TAG}
docker push amrox/gc-redis:${TAG}
docker push amrox/webserver:${TAG}
docker push amrox/alert:${TAG}
