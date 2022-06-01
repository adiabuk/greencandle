#pylint: disable=no-member,wrong-import-position

"""
Check that all trading pairs used in various configs exist and have data
"""

import os
import unittest
from greencandle.lib import config
config.create_config()
from greencandle.lib.binance_common import get_binance_klines


class TestPair(unittest.TestCase):
    """Test executables included in package"""

    @staticmethod
    def test_pair():
        """
        test all trading pairs
        """

        envs = []
        pairs = []
        yamls = ['install/docker-compose_stag.yml', 'install/docker-compose_prod.yml',
                 'install/docker-compose_test.yml', 'install/docker-compose_data.yml']

        for env in yamls:
            # Extract all config_envs from yaml files
            content = open(env, 'r').readlines()

            for line in content:
                if "CONFIG_ENV" in line:
                    envs.append(line.split('=')[-1].strip())

        for item in envs:
            # Extract pairs from each environment except top level
            if '/' in item:
                extracted = os.popen('configstore package get {} pairs'.format(item)).read().split()
                pairs.extend(extracted)


        for pair in set(pairs):
            # Attempt to get data for each unique pair
            if pair not in ("None", "any"):
                print("Testing pair " + pair)
                get_binance_klines(pair, '1m', 1)
