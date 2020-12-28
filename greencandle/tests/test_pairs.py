#pylint: disable=no-member,wrong-import-position

"""
Check that all trading pairs used in various configs exist and have data
"""

import os
from greencandle.lib import config
config.create_config()
from greencandle.lib.binance_common import get_binance_klines
li = []
pairs = []
yamls = ['install/docker-compose_stag.yml', 'install/docker-compose_prod.yml']

for env in yamls:
    # Extract all config_envs from yaml files
    content = open(env, 'r').readlines()

    for line in content:
        if "CONFIG_ENV" in line:
            li.append(line.split('=')[-1].strip())

for item in li:
    # Extract pairs from each environment except top level
    if '/' in item:
        extracted = os.popen('configstore package get {} pairs'.format(item)).read().split()
        pairs.extend(extracted)


for pair in set(pairs):
    # Attempt to get data for each unique pair
    print("Testing pair " + pair)
    get_binance_klines(pair, '1m',1)
