#!/usr/bin/env bash

apt-get -y install python3 python3-pip mysql-server libmysqlclient-dev redis

update-alternatives --install /usr/bin/python python /usr/bin/python3 1
update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
pip install -r requirements.txt

wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar zxvf ta-lib-0.4.0-src.tar.gz -C /tmp
cd /tmp/ta-lib-0.4.0
./configure --prefix=/usr
make
make install
export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"

