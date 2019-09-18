#pylint: disable=wrong-import-position,no-member,attribute-defined-outside-init,unused-variable

"""
Unittest file for testing results of a run using downloaded data
"""

import unittest
from greencandle.lib import config
config.create_config()

from greencandle.lib.logger import getLogger
from greencandle.lib.mysql import Mysql
from .unittests import OrderedTest

LOGGER = getLogger(__name__, config.main.logging_level)

class TestMysql(OrderedTest):
    """Test mysql class methods"""
    def setUp(self):
        """
        Define static instance variables and create redis/mysql objects as well as working test
        directory
        """
        LOGGER.info("Setting up environment")
        self.dbase = Mysql(test=True, interval="1h")

    def step_1(self):
        """Test good and bad query"""
        with self.assertRaises(Exception) as context:
            cur = self.dbase.dbase.cursor()
            self.dbase.execute(cur, 'select dasdasdas')
        self.assertIn('Unknown column', str(context.exception))
        self.dbase.execute(cur, 'select * from trades')

    def step_2(self):
        """Check insert and update trades"""

        self.date = '2018-05-07 22:44:59'
        self.sell_date = '2018-05-07 22:44:59'
        self.pair = 'XXXYYY'
        self.dbase.insert_trade(self.pair, self.date, 100, 20, 30)


        buy_time, sell_time, pair, interval, buy_price, sell_price, investment, total = \
                self.dbase.fetch_sql_data('select * from trades')[-1]
        current_time = buy_time.strftime("%Y-%m-%d %H:%M:%S")
        assert current_time == self.date
        assert sell_time is None
        self.dbase.update_trades(self.pair, self.sell_date, 500)
        buy_time, sell_time, pair, interval, buy_price, sell_price, investment, total = \
                self.dbase.fetch_sql_data('select * from trades')[-1]
        assert sell_time is not None

    def tearDown(self):
        del self.dbase


if __name__ == '__main__':
    unittest.main()
