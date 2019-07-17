#!/usr/bin/env bash

apt-get -y update
apt-get -y install docker.io ntpdate

docker build -f /vagrant/Dockerfile-gc . --tag=greencandle-test

docker build -f /vagrant/Dockerfile-ms . --tag=mysql
docker run -p 3306:3306 -d -e MYSQL_ROOT_PASSWORD=password mysql

mysql --protocal tcp -h localhost -uroot -ppassword < /vagrant/greencandle.sql
docker build -f /vagrant/Dockerfile-rs . --tag=redis
docker run -p 6379:6379 -d redis

#docker run -d greencandle-test

