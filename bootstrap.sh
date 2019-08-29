#!/usr/bin/env bash

set -xe

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Setup local env
apt-get -y update
apt-get -y install docker.io ntpdate mysql-client screen
curl -L https://github.com/docker/compose/releases/download/1.24.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
[[ ! -f config.ini ]] && cp config.ini.sample config.ini

sudo systemctl unmask docker.service
sudo systemctl unmask docker.socket
sudo systemctl start docker.service

usermod -aG docker ubuntu && newgrp docker || true

echo "127.0.0.1    mysql" >> /etc/hosts
echo "127.0.0.1    redis" >> /etc/hosts

# Build Images
docker build --force-rm --no-cache -f ./Dockerfile-gc . --tag=greencandle
docker build --force-rm --no-cache -f ./Dockerfile-ms . --tag=vanilla-mysql
docker build --force-rm --no-cache -f ./Dockerfile-rs . --tag=gc-redis

docker run -p 3306:3306 -e MYSQL_ROOT_PASSWORD=password -d vanilla-mysql
sleep 20
mysql --protocol=tcp  -uroot -ppassword  -e "create database greencandle"
mysql --protocol=tcp  -uroot -ppassword  -e "create database greencandle_test"
mysql --protocol=tcp  -uroot -ppassword  -e "CREATE USER 'greencandle'@'%' IDENTIFIED BY 'password';"
mysql --protocol=tcp  -uroot -ppassword  -e "GRANT ALL PRIVILEGES ON *.* TO 'greencandle'@'%' WITH GRANT OPTION;"
greencandle/scripts/get_db_schema.sh -p -f ./greencandle.sql
container=$(docker ps|grep mysql|awk {'print $1'})
docker commit $container gc-mysql
docker stop $container

# Cleanup docker env
docker rm $container
docker image rm vanilla-mysql

# Create shared volume
docker volume create data
