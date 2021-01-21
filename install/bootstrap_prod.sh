#!/usr/bin/env bash

set -xe

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

apt-get update
apt-get install software-properties-common
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CC86BB64
add-apt-repository ppa:rmescandon/yq -y

# Setup local env
apt-get -y update
apt-get -y install docker.io ntpdate mysql-client screen atop jq iotop ntp awscli vim atop htop automake autotools-dev fuse g++ git libcurl4-gnutls-dev libfuse-dev libssl-dev libxml2-dev make pkg-config yq
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

#wget https://github.com/motns/configstore/releases/download/v2.5.0/configstore-2.5.0-linux-amd64.tar.gz -P /tmp
wget "https://www.dropbox.com/sh/l22jyonei087h4o/AAChfqr_j4ydTDjILz0Q62Y2a/configstore-2.5.0-linux-amd64.tar.gz?dl=0" -O /tmp/configstore-2.5.0-linux-amd64.tar.gz
tar zxvf /tmp/configstore-2.5.0-linux-amd64.tar.gz -C /usr/local/bin
rm -rf /tmp/configstore-2.5.0-linux-amd64.tar.gz

subdomain=$(configstore package get prod loggly_subdomain)
token=$(configstore package get prod loggly_token)
username=$(configstore package get prod loggly_username)
password=$(configstore package get prod loggly_password)

curl -O https://www.loggly.com/install/configure-linux.sh
sudo bash configure-linux.sh -a $subdomain -t $token -u $username -p $password

#curl -L https://github.com/docker/compose/releases/download/1.24.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
wget "https://www.dropbox.com/sh/l22jyonei087h4o/AADJZi6xGYsn18CSy_hGmQz-a/docker-compose-1.24.1?dl=0" -O /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
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

reboot
