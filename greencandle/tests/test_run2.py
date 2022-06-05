#pylint: disable=unnecessary-pass,too-few-public-methods

"""
Unittest file for testing results of a run using downloaded data
"""
import unittest
from .unittests import make_test_case

class TestCOTIUSDT(make_test_case('unit/scalp', 'COTIUSDT', '15m', '2020-03-01', 10, 31, 6, -0.39,
                                  27.2, 46.0)):
    """test COTIUSDT scalp with ST/TP/TSL"""
    pass

class TestBTCUSDT(make_test_case('unit', 'BTCUSDT', '1h', '2019-05-05', 15, 27, 11, -6.6,
                                 56.39999999999999, 15.2)):

    """Test BTCUSDT"""
    pass

if __name__ == '__main__':
    unittest.main(verbosity=6)
