#!/usr/bin/env bash

export BRANCH=master
export COMMIT=`git rev-parse HEAD`
export DATE=`date`

docker build -t amrox/dashboard:latest -f  install/Dockerfile-ds .
docker build -t amrox/greencandle:latest -f  install/Dockerfile-gc .
docker build -t amrox/gc-mysql:latest -f  install/Dockerfile-ms .
docker build -t amrox/gc-redis:latest -f  install/Dockerfile-rs .
docker build -t amrox/webserver:latest -f  install/Dockerfile-wb .
docker push amrox/greencandle:latest
docker push amrox/webserver:latest
docker push amrox/dashboard:latest
docker push amrox/gc-redis:latest
docker push amrox/gc-mysql:latest
