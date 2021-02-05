#!/usr/bin/env bash

export BRANCH=1.7.1
export COMMIT=`git rev-parse HEAD`
export DATE=`date`

docker build -t amrox/dashboard:release-1.7.1 -f  install/Dockerfile-ds .
docker build -t amrox/greencandle:release-1.7.1 -f  install/Dockerfile-gc .
docker build -t amrox/gc-mysql:release-1.7.1 -f  install/Dockerfile-ms .
docker build -t amrox/gc-redis:release-1.7.1 -f  install/Dockerfile-rs .
docker build -t amrox/webserver:release-1.7.1 -f  install/Dockerfile-wb .
docker push amrox/greencandle:release-1.7.1
docker push amrox/webserver:release-1.7.1
docker push amrox/dashboard:release-1.7.1
docker push amrox/gc-redis:release-1.7.1
docker push amrox/gc-mysql:release-1.7.1
