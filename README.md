[![Build Status](https://travis-ci.org/adiabuk/greencandle.svg?branch=master)](https://travis-ci.org/adiabuk/greencandle) 
 
 sudo apt-get install libcanberra-gtk-module
sudo apt-get install firefox xvfb

$ wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
$ tar xvfz ta-lib-0.4.0-src.tar.gz
$ cd ta-lib-0.4.0
$ ./configure
$ make
$ make install

pip install quandl

PyQT4:
apt-get install qt4-qmake libqt4-dev
https://gist.github.com/0x414A/8b64178e69d9f8331938

sudo apt-get install mysql-server  libmysqlclient-dev
for redis:
sysctl -w net.core.somaxconn=1024
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=512
sudo sysctl -w net.ipv4.tcp_fin_timeout=30
sudo sysctl -w net.ipv4.ip_local_port_range="15000 61000"
sudo sysctl net.ipv4.tcp_tw_reuse =1
mysql:
set global max_connections = 1000;
