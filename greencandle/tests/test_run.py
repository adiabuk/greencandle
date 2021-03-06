#pylint: disable=unnecessary-pass,too-few-public-methods

"""
Unittest file for testing results of a run using downloaded data
"""
import unittest
from .unittests import make_test_case

class TestBNBETH(make_test_case('unit', 'BNBETH', '1h', '2019-02-27', 15, 35, 14, -5.5,
                                64.2, 12.8)):
    """Test BNBETH"""
    pass

class TestLRCBTC(make_test_case('unit', 'LRCBTC', '1h', '2019-01-08', 15, 20, 12, -8.5,
                                99.5, 36.9)):
    """Test LRCBTC"""
    pass

class TestRCNBNB(make_test_case('unit', 'RCNBNB', '1h', '2019-03-29', 15, 22, 23, -5,
                                60.7, 9.3)):
    """Test RCNBNB"""
    pass

class TestCOTIUSDT(make_test_case('unit/scalp', 'COTIUSDT', '15m', '2020-03-01', 10, 31, 6, -0.39,
                                  27.2, 46.1)):
    """test COTIUSDT scalp with ST/TP/TSL"""
    pass

class TestBTCUSDT(make_test_case('unit', 'BTCUSDT', '1h', '2019-05-05', 15, 27, 11, -6.6,
                                 56.39999999999999, 15.2)):

    """Test BTCUSDT"""
    pass

if __name__ == '__main__':
    unittest.main(verbosity=6)
