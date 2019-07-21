#!/usr/bin/env bash

apt-get -y update
apt-get -y install docker.io ntpdate mysql-client
curl -L https://github.com/docker/compose/releases/download/1.24.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

docker build -f /vagrant/Dockerfile-gc . --tag=greencandle
docker build -f /vagrant/Dockerfile-ms . --tag=gc-mysql
docker build -f /vagrant/Dockerfile-rs . --tag=gc-redis


cd /vagrant/docker
docker-compose up -d mysql
mysql --protocol tcp -h localhost -uroot -ppassword < ./greencandle.sql
docker-compose up -d
