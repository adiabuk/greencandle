#!/usr/bin/env bash

set -e

if [[ -z $GIT_BRANCH ]]; then
  TAG="latest"
elif [[ $GIT_BRANCH == "master" ]]; then
  TAG="latest";
else
  TAG="release-${GIT_BRANCH}"
fi

 docker image inspect amrox/greencandle:${TAG} || docker build -f install/Dockerfile-gc . -t amrox/greencandle:${TAG}
 docker image inspect amrox/gc-mysql:${TAG} || docker build -f install/Dockerfile-ms . -t amrox/gc-mysql:${TAG}
 docker image inspect amrox/gc-redis:${TAG} || docker build -f install/Dockerfile-rs . -t amrox/gc-redis:${TAG}
 docker image inspect amrox/webserver:${TAG} || docker build -f install/Dockerfile-wb . -t amrox/webserver:${TAG}
 docker image inspect amrox/alert:${TAG} || docker build -f install/Dockerfile-as . -t amrox/alert:${TAG}

docker push amrox/greencandle:${TAG}
docker push amrox/gc-mysql:${TAG}
docker push amrox/gc-redis:${TAG}
docker push amrox/webserver:${TAG}
docker push amrox/alert:${TAG}
