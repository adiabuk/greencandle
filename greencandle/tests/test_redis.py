#pylint: disable=wrong-import-position,no-member
"""Redis tests"""

import unittest
import time
from greencandle.lib import config
config.create_config()

from greencandle.lib.logger import get_logger
from greencandle.lib.redis_conn import Redis

LOGGER = get_logger(__name__)

class TestRedis(unittest.TestCase):
    """
    Test redis methods
    """

    def test_high_price(self):
        """
        Test setting, retrieving, deleting high price in redis
        """

        pair = 'ETHBTC'
        interval = '1m'
        price = 12
        redis = Redis()

        result = redis.get_high_price(pair, interval)
        self.assertIsNone(result)

        redis.put_high_price(pair, interval, price)
        result = redis.get_high_price(pair, interval)
        self.assertEqual(result, price)

        redis.del_high_price(pair, interval)
        result = redis.get_high_price(pair, interval)
        self.assertIsNone(result)
        del redis

    def test_get_items(self):
        """
        Test putting/getting items to/from redis
        """

        redis = Redis()
        items = redis.get_items('ABCDEF', '10m')
        self.assertEqual(len(items), 0)

        redis.redis_conn('ETHBTC', '1m', {"a":1}, time.time())
        items = redis.get_items('ABCDEF', '10m')
        self.assertEqual(len(items), 0)

        items = redis.get_items('ETHBTC', '1m')
        self.assertEqual(len(items), 1)

        redis.redis_conn('ETHBTC', '1m', {"a":1}, time.time())
        items = redis.get_items('ETHBTC', '1m')
        self.assertEqual(len(items), 2)

        for _ in range(10):
            redis.redis_conn('ETHBNB', '1m', {"a":1}, time.time())
            time.sleep(1)
        items = redis.get_items('ETHBNB', '1m')
        self.assertEqual(len(items), 10)
        redis.clear_all()
        del redis

MODULES=["test_redis"]
def start_test():
    """ run unit tests """
    test_suite = []
    for module in MODULES:
        test_suite.extend(unittest.TestLoader().loadTestsFromModule(
            globals()[module]))

    test_suite = unittest.suite.TestSuite(test_suite)
    runner = unittest.TextTestRunner()
    result = runner.run(test_suite)
    total = result.testsRun
    failed = len(result.errors) + len(result.failures)
    perc = 100 - (100*float(failed)/total)
    return perc

