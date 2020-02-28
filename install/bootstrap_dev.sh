#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

set -xe

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Setup local env
apt-get -y update
apt-get -y install docker.io ntpdate mysql-client screen atop jq iotop ntp awscli vim \
    wget make git mysql-client libmysqlclient-dev python3-dev xvfb firefox redis-tools \
    cron bsdmainutils libssl-dev gcc libsystemd-dev
curl -L https://github.com/docker/compose/releases/download/1.24.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
echo "export HOSTNAME >> ~/.bashrc"

# Install Python 3.7.0 with pyenv
apt-get install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl

rm -rf /opt/pyenv ||true  # for travisci
export PYENV_ROOT="/opt/pyenv"
curl https://pyenv.run | bash

cat << \EOF >> ~/.bashrc
export ConEmuDefaultCp=65001
export PYTHONIOENCODING=utf-8
if [ -d "/opt/pyenv" ]; then
 export PYENV_ROOT="/opt/pyenv"
 PYENV_BIN=/opt/pyenv/versions/3.7.0/bin/
 export PATH="$PYENV_BIN:$PYENV_ROOT/bin:$PATH"
 eval "$(pyenv init -)"
fi
EOF


export PYENV_ROOT="/opt/pyenv"
PYENV_BIN=/opt/pyenv/versions/3.7.0/bin/
export PATH="$PYENV_BIN:$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

pyenv install 3.7.0
pyenv global 3.7.0
chmod o+w /opt/pyenv/shims /opt/pyenv/versions

if [[ ! -f /usr/local/bin/configstore ]]; then
    wget https://github.com/motns/configstore/releases/download/v2.4.0/configstore-2.4.0-linux-amd64.tar.gz -P /tmp
    tar zxvf /tmp/configstore-2.4.0-linux-amd64.tar.gz -C /usr/local/bin
    rm -rf /tmp/configstore-2.4.0-linux-amd64.tar.gz
fi

if [[ ! -d /usr/include/ta-lib ]]; then
  wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz -P /tmp
  tar zxvf /tmp/ta-lib-0.4.0-src.tar.gz -C /tmp
  cd /tmp/ta-lib
  ./configure --prefix=/usr
  make
  make install
  cd -
  rm -rf /tmp/ta-lib
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
install_dir=/srv/greencandle
[[ ! -d $install_dir ]] && ln -s /home/travis/build/adiabuk/greencandle/ $install_dir
cd $install_dir
python ./setup.py install
pip install pytest redis-dump-load gitpython setuptools==45.1.0
