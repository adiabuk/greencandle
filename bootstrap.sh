#!/usr/bin/env bash

apt-get -y update
apt-get -y install docker.io

docker build -f /vagrant/Dockerfile-gc . --tag=greencandle-test
docker build -f /vagrant/Dockerfile-ms . --tag=mysql
mysql -uroot -pmy-secret-pw < /tmp/greencandle.sql
docker build -f /vagrant/Dockerfile-rs . --tag=redis

docker run greencandle-test -d
docker run mysql -d
docker run redis -d

