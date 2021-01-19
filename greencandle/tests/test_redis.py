#pylint: disable=wrong-import-position,no-member
"""Redis tests"""

import unittest
import random
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

    def test_get_items(self):
        """
        Test putting/getting items to/from redis
        """

        redis = Redis()
        redis.clear_all()
        items = redis.get_items('ABCDEF', '10m')
        self.assertEqual(len(items), 0)

        redis.redis_conn('ETHBTC', '1m', {"a":1},1607896214)
        items = redis.get_items('ABCDEF', '10m')
        self.assertEqual(len(items), 0)

        items = redis.get_items('ETHBTC', '1m')
        self.assertEqual(len(items), 0)

        redis.redis_conn('ETHBTC', '1m', {"a":1}, 1609108999)
        items = redis.get_items('ETHBTC', '1m')
        self.assertEqual(len(items), 1)

        def random_epoch():
            start_time = int(time.time())
            end_time = start_time + 5184000    # 60 days
            time_str=str(random.randint(start_time, end_time))
            time_str.replace(" ", "").rstrip(time_str[-3:]).upper()
            return int(time_str[:-3] +'999')

        for _ in range(10):
            redis.redis_conn('ETHBNB', '1m', {"a":1}, random_epoch())
            time.sleep(1)
        items = redis.get_items('ETHBNB', '1m')
        self.assertEqual(len(items), 10)
        redis.clear_all()
        del redis
