#pylint: disable=wrong-import-position,no-member
"""Redis tests"""

import os
import unittest
import time
import pandas as pd
from greencandle.lib import config
config.create_config()

from greencandle.lib.logger import get_logger
from greencandle.lib.redis_conn import Redis

LOGGER = get_logger(__name__)

class TestDraw(unittest.TestCase):
    """
    Test redis methods
    """
    @staticmethod
    def create_series(data):
        """
        Create pandas series representing a single candle using given data
        """
        return pd.DataFrame(data, columns=['closeTime', 'open', 'high', 'low',
                                           'close']).iloc[-1].astype(float)

    def test_long_drawdown(self):
        """
        Test drawdown
        """

        os.system("configstore package process_templates unit /etc")
        config.create_config()
        pair = 'BTCUSDT'
        redis = Redis(test_data=True)
        redis.clear_all()

        # Initial data - no intial drawdown
        data = {'closeTime':  [1], 'open': [100], 'high': [200], 'low': [300], 'close': [100]}
        redis.update_drawdown(pair, self.create_series(data), 'open')
        self.assertEqual(abs(redis.get_drawdown(pair)['perc']), 0)
        time.sleep(1)
        # Close price 90% lower
        data = {'closeTime':  [2], 'open': [3], 'high': [4], 'low': [10], 'close': [10]}
        redis.update_drawdown(pair, self.create_series(data))
        self.assertEqual(abs(redis.get_drawdown(pair)['perc']), 90)

        time.sleep(1)
        # Close price higher - no change in drawdown
        data = {'closeTime':  [3], 'open': [100], 'high': [200], 'low': [300], 'close': [100]}
        redis.update_drawdown(pair, self.create_series(data))
        self.assertEqual(abs(redis.get_drawdown(pair)['perc']), 90)

        time.sleep(1)
        # Close price higher - no change in drawdown
        data = {'closeTime':  [4], 'open': [200], 'high': [300], 'low': [500], 'close': [200]}
        redis.update_drawdown(pair, self.create_series(data))
        self.assertEqual(abs(redis.get_drawdown(pair)['perc']), 90)

        time.sleep(1)
        # Close price 5% lower than previos low
        data = {'closeTime':  [5], 'open': [200], 'high': [300], 'low': [5], 'close': [2]}
        redis.update_drawdown(pair, self.create_series(data))
        self.assertEqual(abs(redis.get_drawdown(pair)['perc']), 95)

        time.sleep(1)
        # End of trade - 0 drawdown
        redis.rm_drawdown(pair)
        self.assertEqual(abs(redis.get_drawdown(pair)['perc']), 0)

    def test_long_drawup(self):
        """
        Test drawup
        """

        os.system("configstore package process_templates unit /etc")
        config.create_config()
        pair = 'BTCUSDT'
        redis = Redis(test_data=True)
        redis.clear_all()

        # Initial data - no intial drawup
        data = {'closeTime':  [1], 'open': [100], 'high': [200], 'low': [300], 'close': [100]}
        redis.update_drawup(pair, self.create_series(data), 'open')
        self.assertEqual(abs(redis.get_drawup(pair)['perc']), 0)

        time.sleep(1)
        # Close price 90% lower, no change in drawup
        data = {'closeTime':  [2], 'open': [3], 'high': [4], 'low': [10], 'close': [10]}
        redis.update_drawup(pair, self.create_series(data))
        self.assertEqual(abs(redis.get_drawup(pair)['perc']), 0)

        time.sleep(1)
        # High price equal to opening price, no change in drawup
        data = {'closeTime':  [3], 'open': [100], 'high': [100], 'low': [300], 'close': [100]}
        redis.update_drawup(pair, self.create_series(data))
        self.assertEqual(abs(redis.get_drawup(pair)['perc']), 0)

        time.sleep(1)
        # Double initial price (high)
        data = {'closeTime':  [4], 'open': [200], 'high': [200], 'low': [500], 'close': [200]}
        redis.update_drawup(pair, self.create_series(data))
        self.assertEqual(float(redis.get_drawup(pair)['price']), 200)
        self.assertEqual(abs(redis.get_drawup(pair)['perc']), 100)

        time.sleep(1)
        # ?
        data = {'closeTime':  [4], 'open': [800], 'high': [500], 'low': [500], 'close': [300]}
        redis.update_drawup(pair, self.create_series(data))
        self.assertEqual(abs(redis.get_drawup(pair)['perc']), 400)

        time.sleep(1)
        # End of trade - 0 drawdup
        redis.rm_drawup(pair)
        self.assertEqual(abs(redis.get_drawup(pair)['perc']), 0)
