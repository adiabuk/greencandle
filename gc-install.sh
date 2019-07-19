#!/usr/bin/env bash

set -e

wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz -P /tmp
tar zxvf /tmp/ta-lib-0.4.0-src.tar.gz -C /tmp
cd /tmp/ta-lib
./configure --prefix=/usr
make
make install
pip install pip==9.0.1 numpy==1.16.0
#pip install -e git+https://github.com/adiabuk/greencandle.git#egg=greencandle
cd /install
#python ./setup.py install
pip install . --src /tmp
pip install -e git+https://github.com/adiabuk/Technical-Indicators.git#egg=indicator
pip install -e git+https://github.com/adiabuk/binance#egg=binance
echo "Installation Complete"
