#pylint: disable=wrong-import-position,no-member,protected-access
"""Redis TP/TSL and SL tests"""

import os
import unittest
from greencandle.lib import config
config.create_config()

from greencandle.lib.logger import get_logger
from greencandle.lib.redis_conn import Redis

LOGGER = get_logger(__name__)

class TestStopMethods(unittest.TestCase):
    """
    Test Trailing stop/stop loss/take profit
    """

    def test_long_trailing_stop_loss(self):
        """
        Test trailing stop loss for long trades
        """

        config_env = 'unit/scalp'
        os.system("configstore package process_templates {} /etc".format(config_env))
        config.create_config()
        redis = Redis(test=True, test_data=True)

        # current_high <= subperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(current_price=100, high_price=500,
                                                 current_high=2, open_price=400)
        self.assertTrue(result)

        # current_price <=  subperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(current_price=1000, high_price=500,
                                                 current_high=2000, open_price=4000)
        self.assertFalse(result)

        # current_price <=  subperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(current_price=90, high_price=500,
                                                 current_high=2000, open_price=4000)
        self.assertTrue(result)

        # current_price <=  subperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(current_price=90, high_price='',
                                                 current_high=2000, open_price=4000)
        print(result) # False
        self.assertFalse(result)


        redis = Redis(test=True, test_data=False)
        # current_price <=  subperc(trailing_perc, high_price)
        # and current_price > addperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(current_price=90, high_price=500,
                                                 current_high=2000, open_price=4000)
        self.assertFalse(result)

        # current_price <=  subperc(trailing_perc, high_price)
        # and current_price > addperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(current_price=3000, high_price=500,
                                                 current_high=2000, open_price=4000)
        self.assertFalse(result)

        # current_price <=  subperc(trailing_perc, high_price) 498 <= (500-0.1%) ~499.5
        # and current_price > addperc(trailing_start, open_price)
        result = redis._Redis__get_trailing_stop(current_price=498, high_price=500,
                                                 current_high=4000, open_price=200)
        self.assertTrue(result)

        # current_price <=  subperc(trailing_perc, high_price) 498 <= (500-0.1%) ~499.5
        # and current_price > addperc(trailing_start, open_price)
        result = redis._Redis__get_trailing_stop(current_price=498, high_price=500,
                                                 current_high=4000, open_price=300)
        self.assertTrue(result)

        config_env = 'unit/scalp/alt'
        os.system("configstore package process_templates {} /etc".format(config_env))

        config.create_config()
        #changes  check to current_high (from current_price)
        redis = Redis(test=True, test_data=True)

        # current_high <=  subperc(trailing_perc, high_price)
        # and current_price > addperc(trailing_start, open_price)
        result = redis._Redis__get_trailing_stop(current_price=498, high_price=500,
                                                 current_high=4000, open_price=300)
        self.assertFalse(result)

        # current_high <=  subperc(trailing_perc, high_price)
        # and current_price > addperc(trailing_start, open_price)
        result = redis._Redis__get_trailing_stop(current_price=498, high_price=600,
                                                 current_high=4000, open_price=300)
        self.assertFalse(result)
        #######

        #######
        # current_high <=  subperc(trailing_perc, high_price)
        # and current_price > addperc(trailing_start, open_price)
        result = redis._Redis__get_trailing_stop(current_price=498, high_price=4000,
                                                 current_high=600, open_price=300)
        self.assertTrue(result)

    def test_long_stop_loss(self):
        """
        Test stop loss for long trades
        """

        config_env = 'unit/scalp'
        os.system("configstore package process_templates {} /etc".format(config_env))
        config.create_config()
        redis = Redis(test=True, test_data=True)

        # current_low < open_price - stop_perc 10%
        result = redis._Redis__get_stop_loss(current_price=100, current_low=100,
                                             open_price=400)
        self.assertTrue(result)

        # current_low < open_price - stop_perc 10%
        result = redis._Redis__get_stop_loss(current_price=359, current_low=500,
                                             open_price=400)
        self.assertFalse(result)

        config_env = 'unit/scalp/alt'
        redis = Redis(test=True, test_data=False)
        # turn off immediate stop - changes check to current_price

        # current_price < open_price - stop_perc 10%
        result = redis._Redis__get_stop_loss(current_price=364, current_low=500,
                                             open_price=400)
        self.assertFalse(result)

        # current_price < open_price - stop_perc 10%
        result = redis._Redis__get_stop_loss(current_price=200, current_low=500,
                                             open_price=400)
        self.assertTrue(result)

        # no open price - return False
        result = redis._Redis__get_stop_loss(current_price=200, current_low=500,
                                             open_price='')
        self.assertFalse(result)

    def test_long_take_profit(self):
        """
        Test stop loss for long trades
        """

        config_env = 'unit/scalp'
        os.system("configstore package process_templates {} /etc".format(config_env))
        config.create_config()
        redis = Redis(test=True, test_data=True)

        # current_high > addperc(profit_perc, open_price)  10%
        result = redis._Redis__get_take_profit(current_price=200, current_high=500,
                                               open_price=20)
        self.assertTrue(result)

        # current_high > addperc(profit_perc, open_price)  10%
        result = redis._Redis__get_take_profit(current_price=10, current_high=500,
                                               open_price=20)
        self.assertTrue(result)

        # current_high > addperc(profit_perc, open_price)  10%
        result = redis._Redis__get_take_profit(current_price=10, current_high=1,
                                               open_price=20)
        self.assertFalse(result)

        config_env = 'unit/scalp/alt'
        os.system("configstore package process_templates {} /etc".format(config_env))
        config.create_config()
        redis = Redis(test=True, test_data=False)
        # turn off immediate take profit- changes check to current_price

        # current_price > addperc(profit_perc, open_price)  10%
        result = redis._Redis__get_take_profit(current_price=10, current_high=1,
                                               open_price=20)
        self.assertFalse(result)

        # current_price > addperc(profit_perc, open_price)  10%
        result = redis._Redis__get_take_profit(current_price=100, current_high=1,
                                               open_price=20)
        self.assertTrue(result)
