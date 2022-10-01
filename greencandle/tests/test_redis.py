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
        config.create_config()
        redis = Redis(test_data=True)
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

        for i in loaded_obj.keys():
            loaded_obj[i] = {k.decode() if isinstance(k, bytes) else k: v.decode() \
                    if isinstance(v, bytes) else v for k, v in loaded_obj[i].items()}
            loaded_obj[i] = ast.literal_eval(loaded_obj[i]) if isinstance(loaded_obj[i], str) \
                    else loaded_obj[i]
            for j in loaded_obj[i].keys():

                loaded_obj[i][j] = ast.literal_eval(loaded_obj[i][j]) if \
                        isinstance(loaded_obj[i][j], str) else loaded_obj[i][j]

                loaded_obj[i][j] = {k.decode() if isinstance(k, bytes) else k: v.decode() if \
                        isinstance(v, bytes) and k != 'result' else v for k, v \
                        in loaded_obj[i][j].items()}

            date = loaded_obj[i]['ohlc']['date']
            redis.redis_conn('BTCUSDT', '1h', loaded_obj[i], date)

    def test_get_action(self):
        """
        Test get action method
        """
        pair = "BTCUSDT"
        os.system("configstore package process_templates unit /etc")
        config.create_config()
        quote = get_quote(pair)
        redis = Redis(test_data=True)
        dbase = Mysql(test=True, interval="1h")
        redis.clear_all()
        dbase.delete_data()
        action = redis.get_action(pair, '1h')
        self.assertEqual(action[0], 'HOLD')
        self.assertEqual(action[1], 'Not enough data')
        self.assertEqual(action[2], 0)
        self.assertEqual(action[4]['buy'], [])
        self.assertEqual(action[4]['sell'], [])

        redis.clear_all()
        dbase.delete_data()

        self.insert_data('buy', redis)
        action = redis.get_action(pair, '1h')
        self.assertEqual(action[0], 'OPEN')
        self.assertEqual(action[1], 'long_spot_NormalOPEN')
        self.assertEqual(action[2], '2019-09-03 19:59:59')
        self.assertEqual(action[3], 10647.37)
        self.assertEqual(action[4]['buy'], [1])
        self.assertEqual(action[4]['sell'], [])

        self.insert_data('sell', redis)
        action = redis.get_action(pair, '1h')
        self.assertEqual(action[0], 'NOITEM')
        self.assertEqual(action[1], 'long_spot_NOITEM')
        self.assertEqual(action[2], '2019-09-06 23:59:59')
        self.assertEqual(action[3], 10298.73)
        self.assertEqual(action[4]['buy'], [])
        # Sell rule matched but no item to sell
        self.assertEqual(action[4]['sell'], [1])

        dbase.insert_trade(pair, "2019-09-06 23:59:59", "10647.37", "0.03130663", "333",
                           symbol_name=quote)

        action = redis.get_action(pair, '1h')
        self.assertEqual(action[0], 'CLOSE')
        self.assertEqual(action[1], 'long_spot_NormalCLOSE')
        self.assertEqual(action[2], '2019-09-06 23:59:59')
        self.assertEqual(action[3], 10298.73)
        self.assertEqual(action[4]['buy'], [])
        self.assertEqual(action[4]['sell'], [1])

        dbase.update_trades(pair, "2019-09-07 23:59:59", "10999", "444", "0.03130663",
                            symbol_name=quote)

        self.insert_data('random', redis)
        action = redis.get_action(pair, '1h')
        self.assertEqual(action[0], 'NOITEM')
        self.assertEqual(action[1], 'long_spot_NOITEM')
        self.assertEqual(action[2], '2019-09-16 19:59:59')
        self.assertEqual(action[3], 10121.39)
        self.assertEqual(action[4]['buy'], [])
        self.assertEqual(action[4]['sell'], [1])
