#!/usr/bin/env bash

set -e

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

if [ -f /.dockerenv ]; then
    echo "I'm inside matrix ;(";
    apt-get update
    apt-get -y install cron netcat vim default-mysql-client bsdmainutils
    install_dir=/install
else
    echo "I'm living in real world!";
    cp -rv config /opt
    apt-get update
    apt-get -y install python3 python3-pip wget make git mysql-client libmysqlclient-dev \
      python3-dev xvfb firefox redis-tools cron vim bsdmainutils
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
    pip install ipython
    install_dir=/srv/greencandle
    echo "set background=dark" | tee -a /root/.vimrc /home/ubuntu/.vimrc
    if [[ ! -f /usr/local/bin/gechodriver ]]; then
        wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz -P /tmp
        tar zxvf /tmp/geckodriver-v0.24.0-linux64.tar.gz -C /usr/local/bin
        rm -rf /tmp/geckodriver-v0.24.0-linux64.tar.gz
    fi
fi

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

pip install pip==9.0.1 numpy==1.16.0
cd $install_dir

pip install . --src /tmp
pip install -e git+https://github.com/adiabuk/Technical-Indicators.git#egg=indicator
pip install -e git+https://github.com/adiabuk/binance#egg=binance
[[ ! -d /opt/output ]] && mkdir /opt/output
echo "Installation Complete"
