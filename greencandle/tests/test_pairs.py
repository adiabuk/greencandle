#pylint: disable=no-member,wrong-import-position

"""
Check that all trading pairs used in various configs exist and have data
"""

import os
import unittest
from greencandle.lib.binance import Binance
from greencandle.lib import config
config.create_config()

class TestPair(unittest.TestCase):
    """Test executables included in package"""

    def test_pair(self):
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

        client = Binance()
        info = client.exchange_info()
        bad_pairs = []
        for pair in set(pairs):
            pair = pair.strip()
            if pair not in ("None", "any"):
                print("Testing pair " + pair)
                self.assertIn(pair, info)
                try:
                    self.assertEqual(info[pair]['status'], 'TRADING')
                except:
                    print(f"FAIL: {pair}")
                    bad_pairs.append(pair)
        if bad_pairs:
            self.fail(f"bad pairs: {bad_pairs}")

