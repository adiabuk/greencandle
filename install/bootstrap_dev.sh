#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

set -xe


if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

env
apt-get update
apt-get -y install software-properties-common gnupg dirmngr ca-certificates apt-transport-https
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CC86BB64

# Setup local env
apt-get -y update
apt-get -y install docker.io netcat ntpdate mysql-client screen atop jq iotop ntp awscli vim \
    wget make git mysql-client libmysqlclient-dev python3-dev xvfb firefox redis-tools \
    cron bsdmainutils libssl-dev gcc libsystemd-dev libjpeg-dev zlib1g-dev wget bsdmainutils

curl -LsS https://downloads.mariadb.com/MariaDB/mariadb_repo_setup | sudo bash -s -- --mariadb-server-version=10.8

mkdir -p /usr/lib/docker/cli-plugins
# download the CLI into the plugins directory
curl -sSL https://github.com/docker/compose/releases/download/v2.9.0/docker-compose-linux-x86_64 -o /usr/lib/docker/cli-plugins/docker-compose
# make the CLI executable
chmod +x /usr/lib/docker/cli-plugins/docker-compose

wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/download/3.0.0-beta/yq_linux_amd64

echo "export HOSTNAME" >> ~/.bashrc

# Install Python 3.7.0 with pyenv
apt-get install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl

export PYENV_ROOT="/opt/pyenv"
curl -s -S -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash

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
    wget "https://www.dropbox.com/sh/l22jyonei087h4o/AAChfqr_j4ydTDjILz0Q62Y2a/configstore-2.5.0-linux-amd64.tar.gz?dl=0" -O /tmp/configstore-2.5.0-linux-amd64.tar.gz
    tar zxvf /tmp/configstore-2.5.0-linux-amd64.tar.gz -C /usr/local/bin
    rm -rf /tmp/configstore-2.5.0-linux-amd64.tar.gz
fi

if [[ ! -d /usr/include/ta-lib ]]; then
  wget "https://www.dropbox.com/sh/l22jyonei087h4o/AABz_MIHb3a8ZPWv0gbhkDAia/ta-lib-0.4.0-src.tar.gz?dl=0" -O /tmp/ta-lib-0.4.0-src.tar.gz
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
    "tag": "{{.Name}}",
    "max-size": "10m",
    "max-file: "3"
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
if [[ -z $GIT_BRANCH ]]; then
  TAG="latest"
elif [[ $GIT_BRANCH == "master" ]]; then
  TAG="latest";
else
  TAG="release-${GIT_BRANCH}"
fi

docker build --force-rm --no-cache -f $DIR/Dockerfile-gc . --tag=amrox/greencandle:${TAG}
#docker build --force-rm --no-cache -f $DIR/Dockerfile-ms . --tag=amrox/gc-mysql:${TAG}
#docker build --force-rm --no-cache -f $DIR/Dockerfile-rs . --tag=amrox/gc-redis:${TAG}
#docker build --force-rm --no-cache -f $DIR/Dockerfile-wb . --tag=amrox/webserver:${TAG}

for app in amrox/gc-mysql amrox/gc-redis amrox/alert amrox/webserver; do
  docker pull ${app}:latest; docker tag ${app}:latest ${app}:${TAG};
done


TAG=$TAG docker compose -f $DIR/docker-compose_dev.yml up -d mysql-unit redis-unit

container=$(docker ps|grep mysql|awk {'print $1'})

# Create shared volume
docker volume create data
mkdir -p /data/{mysql,config,graphs,reports}

# Install outside docker
install_dir=/srv/greencandle
cd $install_dir
pip install setuptools-rust setuptools==45.1.0 pip==9.0.1 numpy==1.16.0 ccxt==1.50.10 cryptography==3.3.1

python ./setup.py install
pip install pytest==6.0.1 redis-dump-load gitpython
ln -sf /usr/share/zoneinfo/Etc/UTC /etc/localtime
