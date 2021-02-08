#!/usr/bin/env bash

set -e

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

if [ -f /.dockerenv ]; then
    echo "I'm inside matrix ;(";
    apt-get update
    apt-get -y install cron netcat default-mysql-client bsdmainutils libssl-dev libsystemd-dev \
      xvfb xauth iceweasel --no-install-recommends
    apt-get clean; apt-get autoclean; rm -rf /var/lib/apt/lists/*
    pip install cython redis-dump-load
    install_dir=/install
else
  echo "I am on a host machine"
fi

if [[ ! -f /usr/local/bin/gechodriver ]]; then
    wget "https://www.dropbox.com/sh/l22jyonei087h4o/AAAVa_B_sDXtWZu17RzazsA2a/geckodriver-v0.26.0-linux64.tar.gz?dl=0" -O /tmp/geckodriver-v0.26.0-linux64.tar.gz
    tar zxvf /tmp/geckodriver-v0.26.0-linux64.tar.gz -C /usr/local/bin
    rm -rf /tmp/geckodriver-v0.26.0-linux64.tar.gz
fi

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
    rm -rf /tmp/ta-lib /tmp/ta-lib-0.4.0-src.tar.gz

fi

pip install pip==9.0.1 numpy==1.16.0 ccxt==1.38.76 cryptography==3.3.1
[[ ! -d $install_dir ]] && ln -s /home/travis/build/adiabuk/greencandle/ $install_dir
cd $install_dir

python ./setup.py install
[[ ! -d /opt/output ]] && mkdir /opt/output
apt-get purge -y gcc g++ g++-8 gcc-8 libx265-165 mercurial-common || true
apt-get -y autoremove
echo "Installation Complete"
