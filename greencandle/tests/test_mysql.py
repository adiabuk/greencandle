#pylint: disable=wrong-import-position,no-member,attribute-defined-outside-init,unused-variable

"""
Unittest file for testing results of a run using downloaded data
"""

import unittest
import time
import datetime
from greencandle.lib.balance_common import get_quote
from greencandle.lib import config
config.create_config()

from greencandle.lib.logger import get_logger
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import perc_diff, add_perc
from .unittests import OrderedTest, get_tag

LOGGER = get_logger(__name__)

class TestMysql(OrderedTest):
    """Test mysql class methods"""
    def setUp(self):
        """
        Define static instance variables and create redis/mysql objects as well as working test
        directory
        """

        LOGGER.info("Setting up environment")
        for container in ['mysql-unit', 'redis-unit']:
            command = ("TAG={} docker compose -f install/docker-compose_unit.yml up -d {}".format(
                get_tag, container))
        time.sleep(6)
        self.dbase = Mysql(test=True, interval="1h")
        self.dbase.delete_data()

    def step_1(self):
        """Check insert and update trades"""

        LOGGER.info("Step 1")
        self.date = '2018-05-07 22:44:59'
        self.sell_date = '2018-05-07 22:44:59'
        self.pair = 'BTCUSDT'
        self.open_price = 100
        self.close_price = 500
        quote_in = 20
        quote = get_quote(self.pair)
        LOGGER.info("Inserting trade")
        self.dbase.insert_trade(self.pair, self.date, self.open_price, quote_amount=quote_in,
                                base_amount=30, symbol_name=quote)
        sql = 'select open_time, close_time from trades'
        open_time, close_time = self.dbase.fetch_sql_data(sql)[-1]
        current_time = open_time.strftime("%Y-%m-%d %H:%M:%S")
        assert current_time == self.date
        assert close_time is None

        base_in = self.dbase.get_quantity(self.pair)
        perc_inc = perc_diff(self.open_price, self.close_price)
        base_out = add_perc(perc_inc, base_in)
        self.dbase.update_trades(self.pair, self.sell_date, self.close_price, quote=quote_in,
                                 base_out=base_out, symbol_name=quote)
        close_time = self.dbase.fetch_sql_data('select close_time from trades')[-1]
        assert close_time is not None

    def step_2(self):
        """
        Test methods
        """
        LOGGER.info("Step 2")
        pair = "XXXYYY"
        date = "2020-10-10"
        months = 12
        max_perc = 20
        recent_high = self.dbase.get_recent_high(pair, date, months, max_perc)
        self.assertFalse(recent_high)
        quantity = self.dbase.get_quantity(pair)
        self.assertIsNone(quantity)
        value = self.dbase.get_trade_value(pair)
        self.assertIs(len(value), 1)
        last_trades = self.dbase.get_last_trades()
        self.assertIs(len(last_trades), 1)
        open_trades = self.dbase.get_trades()
        self.assertIs(len(open_trades), 0)
        rates = self.dbase.get_rates('USDT')
        self.assertIs(len(rates), 2)
        self.assertIs(rates[0], 1)
        self.assertIsInstance(rates[0], int)
        self.assertIsInstance(rates[1], float)
        today = self.dbase.get_todays_profit()
        self.assertIs(len(today), 4)
        self.assertIs(today[0], None)
        self.assertIs(today[1], None)
        self.dbase.get_active_trades()   # No exception
        date1 = (datetime.datetime.now() - datetime.timedelta(minutes=15, hours=1)).strftime("%Y-%m-%d "
                                                                                    "%H:%M:%S")
        date2 = (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%d "
                                                                                 "%H:%M:%S")
        print(date1, date2)
        self.dbase.insert_trade('XXXUSDT', date1, 0, 0, 0, 0, 0, 0, 'short', 'USDT', 0)
        self.dbase.update_trades('XXXUSDT', date2, 0.2, 0.2, 0.2, 'test', 0, 0, 'BNB', 0)

        last_hour_profit = self.dbase.get_last_hour_profit()
        self.assertIs(len(last_hour_profit), 7)
        self.assertIsInstance(last_hour_profit[0], float)
        self.assertIsInstance(last_hour_profit[1], float)
        self.assertIsInstance(last_hour_profit[2], float)
        self.assertIsInstance(last_hour_profit[-1], str)

        now = datetime.datetime.now()
        time_tupple = now.timetuple()
        hour = time_tupple[3]
        last_hour = str(hour - 1)
        self.assertEquals(last_hour_profit[3],0)

if __name__ == '__main__':
    unittest.main()
