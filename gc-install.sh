#!/usr/bin/env bash

set -e

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

if [ -f /.dockerenv ]; then
    echo "I'm inside matrix ;(";
    install_dir=/install
else
    echo "I'm living in real world!";
    apt-get update
    apt-get -y install python3 python3-pip wget make git mysql-client libmysqlclient-dev python3-dev
    pip install ipython
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
    install_dir=/vagrant
    echo "set background=dark" | tee -a /root/.vimrc /home/vagrant/.vimrc
fi

if [[ ! -d /usr/include/ta-lib ]]; then
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz -P /tmp
    tar zxvf /tmp/ta-lib-0.4.0-src.tar.gz -C /tmp
    cd /tmp/ta-lib
    ./configure --prefix=/usr
    make
    make install
fi

pip install pip==9.0.1 numpy==1.16.0
cd $install_dir

pip install . --src /tmp
pip install -e git+https://github.com/adiabuk/Technical-Indicators.git#egg=indicator
pip install -e git+https://github.com/adiabuk/binance#egg=binance
echo "Installation Complete"
