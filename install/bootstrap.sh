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
curl -sS https://download.docker.com/linux/debian/gpg | gpg --dearmor > /usr/share/keyrings/docker-ce.gpg
chmod a+r /usr/share/keyrings/docker-ce.gpg

# Add the repository to Apt sources:
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-ce.gpg] https://download.docker.com/linux/debian $(lsb_release -sc) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Setup local env
apt-get -y update
apt-get -y install wget rsyslog sudo dhcpcd ntpdate screen  jq ntp awscli vim fuse git pkg-config bsdmainutils reptyr psmisc lsof nmap command-not-found packagekit-command-not-found libxml2-utils ipmitool net-tools htop atop iotop dstat mosh ethtool mosh figlet lolcat telnet

apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

apt autoremove --purge -y snapd emacs linux-image-6.1.0-29-amd64 gcc-12 cpp-12 libpcsclite1 dictionaries-common ibritish ienglish-common ispell docutils-common xkb-data
apt-get dist-upgrade -y
apt-get clean; apt-get autoclean; rm -rf /var/lib/apt/lists/*

sed -i '/*.emerg/ s/./#&/' /etc/rsyslog.conf
echo "ForwardToWall=no" >> /etc/systemd/journald.conf
wget "http://local.amrox.loc/files/config/30-greencandle.conf" -O /etc/rsyslog.d/30-greencandle.conf
wget "http://local.amrox.loc/files/configstore-2.5.0-linux-amd64.tar.gz" -O /tmp/configstore-2.5.0-linux-amd64.tar.gz
tar zxvf /tmp/configstore-2.5.0-linux-amd64.tar.gz -C /usr/local/bin
rm -rf /tmp/configstore-2.5.0-linux-amd64.tar.gz

wget -qO /usr/local/bin/yq http://local.amrox.loc/files/yq_3
chmod +x /usr/local/bin/yq
wget -qO /etc/update-motd.d/99-figlet http://local.amrox.loc/files/config/99-figlet

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
echo "amro ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

chmod +x /etc/update-motd.d/99-figlet
wget -qO /etc/systemd/interfaces http://local.amrox.loc/files/config/ens18
mkdir -p /home/amro/.ssh
wget -qO /home/amro/.ssh/authorized_keys http://local.amrox.loc/files/config/authorized_keys
wget -qO /home/amro/.ssh/id_rsa http://local.amrox.loc/files/config/id_rsa
wget -qO /etc/apt/apt.conf.d/02nocache http://local.amrox.loc/files/config/02nocache
rm -rf /var/cache/apt/archives
wget -qO /etc/dpkg/dpkg.cfg.d/01nodoc http://local.amrox.loc/files/config/01nodoc
rm -rf /usr/share/doc/
rm -rf /usr/share/man/
rm -rf /usr/share/locale/


chown amro:amro -R ~amro/.ssh
chmod 600 /home/amro/.ssh/*
usermod -a -G docker amro
touch /var/log/gc_test.log /var/log/gc_stag.log /var/log/gc_prod.log /var/log/gc_per.log /var/log/gc_stream.log;chown root:adm /var/log/gc_stag.log /var/log/gc_prod.log /var/log/gc_per.log /var/log/gc_stream.log

#reboot
