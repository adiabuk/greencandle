#!/usr/bin/env bash

apt-get -y update
apt-get -y install docker.io docker-compose ntpdate mysql-client

docker build -f /vagrant/docker/Dockerfile-gc . --tag=greencandle
docker build -f /vagrant/docker/Dockerfile-ms . --tag=gc-mysql
docker build -f /vagrant/docker/Dockerfile-rs . --tag=gc-redis
