#!/usr/bin/env bash

set -e

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

if [ -f /.dockerenv ]; then
    echo "I'm inside matrix ;(";
    install_dir=/srv/greencandle
else
  echo "I am on a host machine"
fi

[[ ! -d $install_dir ]] && ln -s /home/travis/build/adiabuk/greencandle/ $install_dir
cd $install_dir

python ./setup.py install
[[ ! -d /opt/output ]] && mkdir /opt/output
apt-get purge -y gcc g++ g++-8 gcc-8 libx265-165 mercurial-common || true
apt-get -y autoremove
echo "Installation Complete"
