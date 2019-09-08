#pylint: disable=wrong-import-position

import unittest
import os
from greencandle.lib import config
config.create_config(test=False)
from greencandle.lib.binance_common import get_data
from greencandle.lib.logger import getLogger

LOGGER = getLogger(__name__, config.main.logging_level)

class TestResult(unittest.TestCase):
    def test_config(self):
        self.assertEqual(1, 1)
    def test_get_data(self):
        LOGGER.info("Getting test data")
        pairs = ["BTCUSDT"]
        startdate = "2019-05-01"
        days = 30
        outputdir = "/tmp"
        intervals = ["1h"]

        get_data(startdate, intervals, pairs, days, outputdir)
        filename = outputdir + '/' + pairs[0]+ '_' + intervals[0] + '.p'
        assert os.path.exists(filename) == 1

    def test_serial_run(self):
        LOGGER.info("Executing serial test run")
        assert True

    def test_results(self):
        pass
    def test_cleanup(self):
        pass

if __name__ == '__main__':
    unittest.main()
