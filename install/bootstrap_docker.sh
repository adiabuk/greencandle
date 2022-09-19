#!/usr/bin/env bash

set -e

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

install_dir=/srv/greencandle
cd $install_dir

python ./setup.py install
[[ ! -d /opt/output ]] && mkdir /opt/output
apt-get purge -y gcc g++ g++-8 gcc-8 libx265-165 mercurial-common || true
apt-get -y autoremove
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install --upgrade setuptools==45.1.0
pip install pip==9.0.1
rm get-pip.py
echo "Installation Complete"
