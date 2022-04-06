#pylint: disable=wrong-import-position,no-member,attribute-defined-outside-init,unused-variable

"""
Unittest file for testing results of a run using downloaded data
"""

import os
import unittest
import time
from greencandle.lib.balance_common import get_quote
from greencandle.lib import config
config.create_config()

from greencandle.lib.logger import get_logger
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import perc_diff, add_perc
from .unittests import OrderedTest

LOGGER = get_logger(__name__)

class TestMysql(OrderedTest):
    """Test mysql class methods"""
    def setUp(self):
        """
        Define static instance variables and create redis/mysql objects as well as working test
        directory
        """
        tag = os.environ['TAG']
        LOGGER.info("Setting up environment")
        for container in ['mysql-unit', 'redis-unit']:
            command = ("TAG=$TAG docker-compose -f install/docker-compose_unit.yml up -d "
                       + container)
        time.sleep(6)
        self.dbase = Mysql(test=True, interval="1h")

    def step_1(self):
        """Check insert and update trades"""

        self.date = '2018-05-07 22:44:59'
        self.sell_date = '2018-05-07 22:44:59'
        self.pair = 'BTCUSDT'
        self.open_price = 100
        self.close_price = 500
        quote_in = 20
        quote = get_quote(self.pair)
        self.dbase.insert_trade(self.pair, self.date, self.open_price, quote_amount=quote_in,
                                base_amount=30, quote_name=quote)
        sql = 'select open_time, close_time from trades'
        open_time, close_time = self.dbase.fetch_sql_data(sql)[-1]
        current_time = open_time.strftime("%Y-%m-%d %H:%M:%S")
        assert current_time == self.date
        assert close_time is None

        base_in = self.dbase.get_quantity(self.pair)
        perc_inc = perc_diff(self.open_price, self.close_price)
        base_out = add_perc(perc_inc, base_in)
        self.dbase.update_trades(self.pair, self.sell_date, self.close_price, quote=quote_in,
                                 base_out=base_out, quote_name=quote)
        close_time = self.dbase.fetch_sql_data('select close_time from trades')[-1]
        assert close_time is not None

    def tearDown(self):
        del self.dbase

if __name__ == '__main__':
    unittest.main()
