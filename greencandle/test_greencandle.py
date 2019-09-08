#pylint: disable=wrong-import-position,no-member,broad-except

"""
Unittest file for testing results of a run using downloaded data
"""

import unittest
import os
import shutil
from greencandle.lib import config
config.create_config(test=True)

from greencandle.lib.binance_common import get_data
from greencandle.lib.logger import getLogger
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.backend_test import serial_test

LOGGER = getLogger(__name__, config.main.logging_level)

class TestResult(unittest.TestCase):
    """
    Sequential unit tests which download data from binance, run process, and collect results
    Items checked:
                   * pickle file
                   * mysql/redis connection
                   * results
    """
    def setUp(self):
        """
        Define static instance variables and create redis/mysql objects as well as working test
        directory
        """
        LOGGER.info("Setting up environment")
        self.pairs = ["BTCUSDT"]
        self.startdate = "2019-05-05"
        self.days = 15
        self.outputdir = "/tmp/test_data"
        self.intervals = ["1h"]
        self.redis = Redis(interval=self.intervals[0], test=True, db=1)
        self.dbase = Mysql(test=True, interval=self.intervals[0])
        if not os.path.exists(self.outputdir):
            os.mkdir(self.outputdir)

    def step_1(self):
        """
        Step 1 - get test data
        """

        LOGGER.info("Getting test data")

        get_data(self.startdate, self.intervals, self.pairs, self.days, self.outputdir)
        filename = self.outputdir + '/' + self.pairs[0]+ '_' + self.intervals[0] + '.p'
        assert os.path.exists(filename) == 1

    def step_2(self):
        """
        Step 2 - execute test run
        """
        LOGGER.info("Executing serial test run")
        main_indicators = config.main.indicators.split()
        serial_test(self.pairs, self.intervals, self.outputdir, main_indicators)
        assert True

    def step_3(self):
        """
        Step 3 - collect and compare data
        """
        LOGGER.info("Comparing mysql data")
        db_sum = self.dbase.fetch_sql_data("select sum(perc) from profit", header=False)[0][0]
        db_min = self.dbase.fetch_sql_data("select min(perc) from profit", header=False)[0][0]
        db_max = self.dbase.fetch_sql_data("select max(perc) from profit", header=False)[0][0]
        LOGGER.info(db_sum)
        self.assertGreaterEqual(float(db_sum), 18)
        self.assertGreaterEqual(float(db_max), 10)
        self.assertGreaterEqual(float(db_min), -4.5)

    def _steps(self):
        """
        Get lists of steps that are to be run
        methods should be called "step_n" where n denotes the sequence of execution
        """
        for name in dir(self): # dir() result is implicitly sorted
            if name.startswith("step"):
                yield name, getattr(self, name)

    def test_steps(self):
        """
        Run test steps in sequence
        """
        for _, step in self._steps():
            try:
                step()
            except Exception as exc:
                self.fail("{} failed ({}: {})".format(step, type(exc), exc))

    def tearDown(self):
        """Cleanup DB and files"""
        self.redis.clear_all()
        self.dbase.delete_data()
        del self.redis
        del self.dbase
        shutil.rmtree(self.outputdir)

if __name__ == '__main__':
    unittest.main()
