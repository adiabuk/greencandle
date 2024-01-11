#pylint: disable=no-member

"""
Unittest file for ensuring indicators are functioning, returning data stored in redis, and have
values which are none null/none
"""

import os
import json
import unittest
from greencandle.lib.logger import get_logger
from greencandle.lib.binance_common import get_data
from greencandle.lib.run import perform_data
from greencandle.lib.redis_conn import Redis
from greencandle.lib import config
config.create_config()


LOGGER = get_logger(__name__)

class TestIndicators(unittest.TestCase):
    """Test indicators are returning data"""
    def setUp(self):
        os.system("configstore package process_templates unit/ind /etc")
        self.pair = 'LINKUSDT'
        self.interval = '1h'
        self.path = '/data/test_data'
        get_data('2023-01-01', [self.interval], [self.pair], 1, self.path, extra=0)

    def test_indicators(self):
        """
        Test indicator data in redis
        """
        config.create_config()

        main_indicators = config.main.indicators.split()
        perform_data(self.pair, self.interval, self.path, main_indicators)

        redis = Redis()
        items = redis.get_items(self.pair, self.interval)

        # get last entry from redis
        results = json.loads(redis.get_item('{}:{}'.format(self.pair, self.interval),
                                            items[-1]).decode())
        short_ind_names = []
        # cycle through indicators from config
        for ind in main_indicators:
            split = ind.split(';')
            # get short name used in redis
            short_ind_names.append(split[1] + '_' + split[2].split(',')[0])

        # cycle through indicator short-names
        for ind in short_ind_names:
            # insure value, or all values in returned list
            # are not None for the last entry in redis
            if isinstance(results[ind], list):
                for item in results[ind]:
                    self.assertIsNotNone(item)
            else:
                self.assertIsNotNone(results[ind])

        if __name__ == '__main__':
            unittest.main()
