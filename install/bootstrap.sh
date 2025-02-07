#!/usr/bin/env bash

set -xe

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

apt-get -y update
apt-get -y install software-properties-common
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CC86BB64

# Add Docker's official GPG key:
apt-get -y install ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -sS https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor > /usr/share/keyrings/docker-ce.gpg
chmod a+r /usr/share/keyrings/docker-ce.gpg

# Add the repository to Apt sources:
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-ce.gpg] https://download.docker.com/linux/debian $(lsb_release -sc) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Setup local env
apt-get -y update
apt-get -y install sudo dhcpcd ntpdate default-mysql-client screen  jq ntp awscli vim automake autotools-dev fuse g++ git libssl-dev libxml2-dev make pkg-config bsdmainutils reptyr psmisc lsof nmap command-not-found packagekit-command-not-found libxml2-utils ipmitool smartmontools net-tools htop atop iotop dstat mosh python-is-python3 ethtool python3-pip mosh

apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

apt autoremove --purge -y snapd emacs
apt-get dist-upgrade -y
apt-get clean; apt-get autoclean; rm -rf /var/lib/apt/lists/*

sed -i '/*.emerg/ s/./#&/' /etc/rsyslog.d/50-default.conf
echo "ForwardToWall=no" >> /etc/systemd/journald.conf

wget "http://local.amrox.loc/files/configstore-2.5.0-linux-amd64.tar.gz" -O /tmp/configstore-2.5.0-linux-amd64.tar.gz
tar zxvf /tmp/configstore-2.5.0-linux-amd64.tar.gz -C /usr/local/bin
rm -rf /tmp/configstore-2.5.0-linux-amd64.tar.gz

wget -qO /usr/local/bin/yq http://local.amrox.loc/files/yq_3

echo "export HOSTNAME" >> ~/.bashrc

cat > /etc/docker/daemon.json << EOF
{
    "default-address-pools":[
        {"base":"172.20.0.0/16","size":24},
        {"base":"172.21.0.0/16","size":24}
    ],
  "live-restore": false,
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
#systemctl start atop

ln -sf /usr/share/zoneinfo/Etc/UTC /etc/localtime
apt install python3-pexpect python3-ipython
reboot
