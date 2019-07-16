#!/usr/bin/env bash

set -e

apt-get update
apt-get -y install python3 python3-pip wget make git mysql-client libmysqlclient-dev python3-dev

update-alternatives --install /usr/bin/python python /usr/bin/python3 1
update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz -P /tmp
tar zxvf /tmp/ta-lib-0.4.0-src.tar.gz -C /tmp
cd /tmp/ta-lib
./configure --prefix=/usr
make
make install
cd /vagrant
python setup.py install
