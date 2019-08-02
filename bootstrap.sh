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
docker build --force-rm --no-cache -f ./Dockerfile-gc . --tag=greencandle
docker build --force-rm --no-cache -f ./Dockerfile-ms . --tag=gc-mysql
docker build --force-rm --no-cache -f ./Dockerfile-rs . --tag=gc-redis
docker volume create data

echo "127.0.0.1    mysql" >> /etc/hosts
echo "127.0.0.1    redis" >> /etc/hosts

docker-compose up -d mysql
sleep 30

mysql --protocol=tcp  -uroot -ppassword  -e "create database greencandle"
mysql --protocol=tcp  -uroot -ppassword  -e "create database greencandle_test"
mysql --protocol=tcp  -uroot -ppassword  -e "grant all on *.* to 'greencandle'@'%' identified by 'password' with grant option;"

docker-compose up -d
