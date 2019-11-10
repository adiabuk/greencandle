#!/usr/bin/env bash

set -xe

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Setup local env
apt-get -y update
apt-get -y install docker.io ntpdate mysql-client screen atop jq iotop ntp
curl -L https://github.com/docker/compose/releases/download/1.24.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

if [[ ! -f /usr/local/bin/configstore ]]; then
    wget https://github.com/motns/configstore/releases/download/v2.4.0/configstore-2.4.0-linux-amd64.tar.gz -P /tmp
    tar zxvf /tmp/configstore-2.4.0-linux-amd64.tar.gz -C /usr/local/bin
    rm -rf /tmp/configstore-2.4.0-linux-amd64.tar.gz
fi

cat > /etc/docker/daemon.json << EOF
{
  "live-restore": true,
  "log-driver": "syslog",
  "raw-logs": true,
  "log-opts": {
    "syslog-facility": "local1",
    "tag": "{{.Name}}"
  }
}
EOF

systemctl start ntp
systemctl unmask docker.service
systemctl unmask docker.socket
systemctl start docker.service

usermod -aG docker ubuntu || true

echo "127.0.0.1    mysql" >> /etc/hosts
echo "127.0.0.1    redis" >> /etc/hosts

# Build Images
docker build --force-rm --no-cache -f ./Dockerfile-gc . --tag=greencandle
docker build --force-rm --no-cache -f ./Dockerfile-ms . --tag=gc-mysql
docker build --force-rm --no-cache -f ./Dockerfile-rs . --tag=gc-redis

#sleep 20
#mysql --protocol=tcp  -uroot -ppassword  -e "create database greencandle"
#mysql --protocol=tcp  -uroot -ppassword  -e "CREATE USER 'greencandle'@'%' IDENTIFIED BY 'password';"
#mysql --protocol=tcp  -uroot -ppassword  -e "GRANT ALL PRIVILEGES ON *.* TO 'greencandle'@'%' WITH GRANT OPTION;"
#mysql --protocol=tcp -uroot -ppassword -e "SET GLOBAL sql_mode = 'NO_ENGINE_SUBSTITUTION';"
#greencandle/scripts/get_db_schema.sh -p -f ./greencandle.sql
container=$(docker ps|grep mysql|awk {'print $1'})
#docker commit $container gc-mysql
#docker stop $container

# Cleanup docker env
#docker rm $container
#docker image rm vanilla-mysql

# Create shared volume
docker volume create data
