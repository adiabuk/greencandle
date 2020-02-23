#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

set -xe

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Setup local env
apt-get -y update
apt-get -y install docker.io ntpdate mysql-client screen atop jq iotop ntp awscli vim
curl -L https://github.com/docker/compose/releases/download/1.24.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
echo "export HOSTNAME >> ~/.bashrc"

# Install Python 3.7.0 with pyenv
apt-get install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl

rm -rf /opt/pyenv ||true  # for travisci
curl https://pyenv.run | bash

cat << \EOF >> ~/.bashrc
# Load pyenv automatically by adding
# the following to ~/.bashrc:
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
EOF

export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv install 3.7.0
pyenv global 3.7.0


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
docker build --force-rm --no-cache -f $DIR/Dockerfile-gc . --tag=greencandle
docker build --force-rm --no-cache -f $DIR/Dockerfile-ms . --tag=gc-mysql
docker build --force-rm --no-cache -f $DIR/Dockerfile-rs . --tag=gc-redis
docker build --force-rm --no-cache -f $DIR/Dockerfile-ds . --tag=dashboard
docker build --force-rm --no-cache -f $DIR/Dockerfile-wb . --tag=webserver

container=$(docker ps|grep mysql|awk {'print $1'})

# Create shared volume
docker volume create data
mkdir -p /data/{mysql,config,graphs,report}

# Install outside docker
install/gc-install.sh
pip install pytest redis-dump-load gitpython setuptools==40.4.3
