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
        os.system(f"configstore package process_templates {config_env} /etc")
        config.create_config()
        redis = Redis(test_data=True, db=2)

        # current_high <= subperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(high_price=500, low_price=0,
                                                 ohlc=(400, 2, 0, 100))
        self.assertTrue(result)

        # current_high <=  subperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(high_price=500, low_price=0,
                                                 ohlc=(4000, 2000,0, 1000))

        self.assertFalse(result)

        # current_high <=  subperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(high_price=50000, low_price=0,
                                                 ohlc=(4000, 2000, 0, 90))
        self.assertTrue(result)

        # current_price <=  subperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(high_price='', low_price=0,
                                                 ohlc=(4000,2000,0,90))
        print(result) # False
        self.assertFalse(result)


        redis = Redis(test_data=False, db=2)
        # current_price <=  subperc(trailing_perc, high_price)
        # and current_price > addperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(high_price=500, low_price=0,
                                                 ohlc=(4000,200,0,90))
        self.assertFalse(result)

        # current_price <=  subperc(trailing_perc, high_price)
        # and current_price > addperc(trailing_perc, high_price)
        result = redis._Redis__get_trailing_stop(high_price=500, low_price=0,
                                                 ohlc=(4000,2000,0,3000))
        self.assertFalse(result)

        # current_price <=  subperc(trailing_perc, high_price) 498 <= (500-0.1%) ~499.5
        # and current_price > addperc(trailing_start, open_price)
        result = redis._Redis__get_trailing_stop(high_price=500, low_price=0,
                                                 ohlc=(200,4000,0,498))
        self.assertTrue(result)

        # current_price <=  subperc(trailing_perc, high_price) 498 <= (500-0.1%) ~499.5
        # and current_price > addperc(trailing_start, open_price)
        result = redis._Redis__get_trailing_stop(high_price=500, low_price=0,
                                                 ohlc=(300,4000,0,498))
        self.assertTrue(result)

        config_env = 'unit/scalp/alt'
        os.system(f"configstore package process_templates {config_env} /etc")

        config.create_config()
        #changes  check to current_high (from current_price)
        redis = Redis(test_data=True, db=2)

        # current_high <=  subperc(trailing_perc, high_price)
        # and current_price > addperc(trailing_start, open_price)
        result = redis._Redis__get_trailing_stop(high_price=500, low_price=0,
                                                 ohlc=(300,4000,0,498))
        self.assertFalse(result)

        # current_high <=  subperc(trailing_perc, high_price)
        # and current_price > addperc(trailing_start, open_price)
        result = redis._Redis__get_trailing_stop(high_price=600, low_price=0,
                                                 ohlc=(300,4000,0,498))
        self.assertFalse(result)
        #######

        #######
        # current_high <=  subperc(trailing_perc, high_price)
        # and current_price > addperc(trailing_start, open_price)
        result = redis._Redis__get_trailing_stop(high_price=4000, low_price=0,
                                                 ohlc=(300,600,0,498))
        self.assertTrue(result)

    def xtest_long_stop_loss(self):
        """
        Test stop loss for long trades
        """

        config_env = 'unit/scalp'
        os.system(f"configstore package process_templates {config_env} /etc")
        config.create_config()
        redis = Redis(test_data=True, db=2)

        # current_low < open_price - stop_perc 10%
        result = redis._Redis__get_stop_loss(current_price=100, current_low=100,
                                             open_price=400, pair='BTCUSDT')
        self.assertTrue(result)

        # current_low < open_price - stop_perc 10%
        result = redis._Redis__get_stop_loss(current_price=359, current_low=500,
                                             open_price=400, pair='BTCUSDT')
        self.assertFalse(result)

        config_env = 'unit/scalp/alt'
        redis = Redis(test_data=False, db=2)
        # turn off immediate stop - changes check to current_price

        # current_price < open_price - stop_perc 10%
        redis.update_on_entry('BTCUSDT', 'take_profit_perc', config.main.take_profit_perc)
        redis.update_on_entry('BTCUSDT', 'stop_loss_perc', config.main.stop_loss_perc)
        result = redis._Redis__get_stop_loss(current_price=364, current_low=500,
                                             open_price=400, pair='BTCUSDT')
        self.assertFalse(result)

        # current_price < open_price - stop_perc 10%
        result = redis._Redis__get_stop_loss(current_price=200, current_low=500,
                                             open_price=400, pair='BTCUSDT')
        self.assertTrue(result)

        # no open price - return False
        result = redis._Redis__get_stop_loss(current_price=200, current_low=500,
                                             open_price='', pair='BTCUSDT')
        self.assertFalse(result)

    def xtest_long_take_profit(self):
        """
        Test stop loss for long trades
        """

        config_env = 'unit/scalp'
        os.system(f"configstore package process_templates {config_env} /etc")
        config.create_config()
        redis = Redis(test_data=True, db=2)

        # current_high > addperc(profit_perc, open_price)  10%
        result = redis._Redis__get_take_profit(current_price=200, current_high=500,
                                               open_price=20, pair='BTCUSDT')
        self.assertTrue(result)

        # current_high > addperc(profit_perc, open_price)  10%
        result = redis._Redis__get_take_profit(current_price=10, current_high=500,
                                               open_price=20, pair='BTCUSDT')
        self.assertTrue(result)

        # current_high > addperc(profit_perc, open_price)  10%
        result = redis._Redis__get_take_profit(current_price=10, current_high=1,
                                               open_price=20, pair='BTCUSDT')
        self.assertFalse(result)

        config_env = 'unit/scalp/alt'
        os.system(f"configstore package process_templates {config_env} /etc")
        config.create_config()
        redis = Redis(test_data=False, db=2)
        # turn off immediate take profit- changes check to current_price

        # current_price > addperc(profit_perc, open_price)  10%
        result = redis._Redis__get_take_profit(current_price=10, current_high=1,
                                               open_price=20, pair='BTCUSDT')
        self.assertFalse(result)

        # current_price > addperc(profit_perc, open_price)  10%
        result = redis._Redis__get_take_profit(current_price=100, current_high=1,
                                               open_price=20, pair='BTCUSDT')
        self.assertTrue(result)
