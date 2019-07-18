#!/usr/bin/env bash

apt-get -y update
apt-get -y install docker.io docker-compose ntpdate mysql-client

docker build -f /vagrant/docker/Dockerfile-gc . --tag=greencandle
docker build -f /vagrant/docker/Dockerfile-ms . --tag=gc-mysql
docker build -f /vagrant/docker/Dockerfile-rs . --tag=gc-redis


cd /vagrant/docker
docker-compose up -d mysql
mysql --protocol tcp -h localhost -uroot -ppassword < /tmp/greencandle.sql
docker-compose up -d
