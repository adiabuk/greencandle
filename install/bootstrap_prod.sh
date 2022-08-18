#!/usr/bin/env bash

set -xe

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

apt-get update
apt-get install software-properties-common
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CC86BB64

# Setup local env
apt-get -y update
apt-get -y install docker.io ntpdate mysql-client screen atop jq iotop ntp awscli vim atop htop automake autotools-dev fuse g++ git libcurl4-gnutls-dev libfuse-dev libssl-dev libxml2-dev make pkg-config bsdmainutils
apt autoremove --purge -y snapd emacs
apt-get dist-upgrade -y
apt-get clean; apt-get autoclean; rm -rf /var/lib/apt/lists/*
update-alternatives --install /usr/bin/python python /usr/bin/python3 1

cd /tmp
git clone https://github.com/s3fs-fuse/s3fs-fuse.git
cd s3fs-fuse
./autogen.sh
./configure
make
make install
cd -
rm -rf /tmp/s3fs-fuse

wget "https://www.dropbox.com/sh/l22jyonei087h4o/AAChfqr_j4ydTDjILz0Q62Y2a/configstore-2.5.0-linux-amd64.tar.gz?dl=0" -O /tmp/configstore-2.5.0-linux-amd64.tar.gz
tar zxvf /tmp/configstore-2.5.0-linux-amd64.tar.gz -C /usr/local/bin
rm -rf /tmp/configstore-2.5.0-linux-amd64.tar.gz

mkdir -p /usr/lib/docker/cli-plugins
# download the CLI into the plugins directory
curl -sSL https://github.com/docker/compose/releases/download/v2.9.0/docker-compose-linux-x86_64 -o /usr/lib/docker/cli-plugins/docker-compose
# make the CLI executable
chmod +x /usr/lib/docker/cli-plugins/docker-compose

wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/download/3.0.0-beta/yq_linux_amd64

echo "export HOSTNAME" >> ~/.bashrc

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

# Start services
systemctl start ntp
systemctl unmask docker.service
systemctl unmask docker.socket
systemctl start docker.service
systemctl start atop

usermod -aG docker ubuntu || true

echo "127.0.0.1    mysql" >> /etc/hosts
echo "127.0.0.1    redis" >> /etc/hosts

# Create shared volume
docker volume create data
mkdir -p /data/{mysql,config,graphs,reports}

# Create and mount swap
fallocate -l 1G /swapfile
dd if=/dev/zero of=/swapfile bs=1024 count=1048576
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo "/swapfile swap swap defaults 0 0" >> /etc/fstab
ln -sf /usr/share/zoneinfo/Etc/UTC /etc/localtime
reboot
