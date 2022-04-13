#pylint: disable=wrong-import-position,no-member
"""Redis tests"""

import os
import ast
import unittest
import random
import time
import pickle
from greencandle.lib.balance_common import get_quote
from greencandle.lib import config
config.create_config()

from greencandle.lib.logger import get_logger
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql

LOGGER = get_logger(__name__)

class TestRedis(unittest.TestCase):
    """
    Test redis methods
    """

    def test_get_items(self):
        """
        Test putting/getting items to/from redis
        """
        os.system("configstore package process_templates unit /etc")
        redis = Redis(test_data=True, test=True)
        redis.clear_all()
        items = redis.get_items('ABCDEF', '10m')
        self.assertEqual(len(items), 0)

        redis.redis_conn('ETHBTC', '1m', {"a":1}, 1607896214)
        items = redis.get_items('ABCDEF', '10m')
        self.assertEqual(len(items), 0)

        items = redis.get_items('ETHBTC', '1m')
        self.assertEqual(len(items), 0)

        redis.redis_conn('ETHBTC', '1m', {"a":1}, 1609199999)
        items = redis.get_items('ETHBTC', '1m')
        self.assertEqual(len(items), 1)

        def random_mepoch():
            start_time = int(time.time())
            end_time = start_time + 10368000  # 120 days
            time_str = str(random.randint(start_time, end_time *1000))
            return int(time_str[:-5] +'99999')

        redis.clear_all()
        for i in range(10):
            redis.redis_conn('ETHBNB', '1m', {i:i}, random_mepoch())

        items = redis.get_items('ETHBNB', '1m')
        self.assertEqual(len(items), 10)
        redis.clear_all()
        del redis

    @staticmethod
    def insert_data(name, redis):
        """
        Get test data from pickle files and insert into redis
        """
        with open('greencandle/tests/{}.p'.format(name), 'rb') as handle:
            loaded_obj = pickle.load(handle)

        datas = ["data1", "data2", "data3", "data4", "data5", "data6"]
        for i in datas:
            decoded = loaded_obj[i][b'ohlc'].decode("UTF-8")
            mydata = ast.literal_eval(decoded)
            date = mydata['date']
            redis.redis_conn('BTCUSDT', '4h', loaded_obj[i], date)

    def test_get_action(self):
        """
        Test get action method
        """
        pair = "BTCUSDT"
        quote = get_quote(pair)
        redis = Redis(interval="4h", test_data=True, test=True)
        dbase = Mysql(test=True, interval="4h")
        redis.clear_all()
        dbase.delete_data()
        action = redis.get_action(pair, '4h')
        self.assertEqual(action[0], 'HOLD')
        self.assertEqual(action[1], 'Not enough data')
        self.assertEqual(action[2], 0)
        self.assertEqual(action[4]['buy'], [])
        self.assertEqual(action[4]['sell'], [])

        redis.clear_all()
        dbase.delete_data()

        self.insert_data('buy', redis)
        action = redis.get_action(pair, '4h')
        self.assertEqual(action[0], 'OPEN')
        self.assertEqual(action[1], 'long_spot_NormalOPEN')
        self.assertEqual(action[2], '2019-09-03 19:59:59')
        self.assertEqual(action[3], 10647.37)
        self.assertEqual(action[4]['buy'], [1])
        self.assertEqual(action[4]['sell'], [])

        self.insert_data('sell', redis)
        action = redis.get_action(pair, '4h')
        self.assertEqual(action[0], 'NOITEM')
        self.assertEqual(action[1], 'long_spot_NOITEM')
        self.assertEqual(action[2], '2019-09-06 23:59:59')
        self.assertEqual(action[3], 10298.73)
        self.assertEqual(action[4]['buy'], [])
        # Sell rule matched but no item to sell
        self.assertEqual(action[4]['sell'], [1])

        dbase.insert_trade(pair, "2019-09-06 23:59:59", "10647.37", "0.03130663", "333",
                           quote_name=quote)

        action = redis.get_action(pair, '4h')
        self.assertEqual(action[0], 'CLOSE')
        self.assertEqual(action[1], 'long_spot_NormalCLOSE')
        self.assertEqual(action[2], '2019-09-06 23:59:59')
        self.assertEqual(action[3], 10298.73)
        self.assertEqual(action[4]['buy'], [])
        self.assertEqual(action[4]['sell'], [1])

        dbase.update_trades(pair, "2019-09-07 23:59:59", "10999", "444", "0.03130663",
                            quote_name=quote)

        self.insert_data('random', redis)
        action = redis.get_action(pair, '4h')
        self.assertEqual(action[0], 'NOITEM')
        self.assertEqual(action[1], 'long_spot_NOITEM')
        self.assertEqual(action[2], '2019-09-16 19:59:59')
        self.assertEqual(action[3], 10121.39)
        self.assertEqual(action[4]['buy'], [])
        self.assertEqual(action[4]['sell'], [1])
