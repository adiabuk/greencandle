#!/usr/bin/env bash

set -xe

apt-get -y update
apt-get -y install docker.io ntpdate mysql-client
curl -L https://github.com/docker/compose/releases/download/1.24.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
[[ ! -f config.ini ]] && cp config.ini.sample config.ini

sudo systemctl unmask docker.service
sudo systemctl unmask docker.socket
sudo systemctl start docker.service
sudo systemctl status docker
docker build -f ./Dockerfile-gc . --tag=greencandle
docker build -f ./Dockerfile-ms . --tag=gc-mysql
docker build -f ./Dockerfile-rs . --tag=gc-redis
echo "127.0.0.1    mysql" >> /etc/hosts
echo "127.0.0.1    redis" >> /etc/hosts

docker-compose up -d mysql
mysql --protocol=tcp  -uroot -ppassword  -e "create database greencandle"
mysql --protocol=tcp  -uroot -ppassword  -e "create database greencandle_test"
mysql --protocol=tcp  -uroot -ppassword  -e "grant all on *.* to 'greencandle'@'%' identified by 'password' with grant option;"

mysql --protocol tcp -h localhost -uroot -ppassword greencandle < ./greencandle.sql
mysql --protocol tcp -h localhost -uroot -ppassword greencandle_test < ./greencandle.sql
docker-compose up -d
