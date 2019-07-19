#!/usr/bin/env bash

apt-get -y update
apt-get -y install docker.io docker-compose ntpdate mysql-client

docker build -f /vagrant/Dockerfile-gc . --tag=greencandle
docker build -f /vagrant/Dockerfile-ms . --tag=gc-mysql
docker build -f /vagrant/Dockerfile-rs . --tag=gc-redis


cd /vagrant/docker
docker-compose up -d mysql
mysql --protocol tcp -h localhost -uroot -ppassword < ./greencandle.sql
docker-compose up -d
