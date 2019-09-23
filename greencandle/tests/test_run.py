#pylint: disable=unnecessary-pass

"""
Unittest file for testing results of a run using downloaded data
"""
import unittest
from .unittests import make_test_case


class TestBTCUSDT(make_test_case('BTCUSDT', '2019-05-05', 18, 10, -4.5)):
    """Test BTCUSDT"""
    pass

class TestBNBETH(make_test_case('BNBETH', '2019-02-27', 18, 10, -4.5)):
    """Test BNBETH"""
    pass

class TestLRTBTC(make_test_case('LRTBTC', '2019-01-18', 18, 10, -5)):
    """Test BNBETH"""
    pass

class TestRCNBNB(make_test_case('RCNBNB', '2019-03-29', 18, 10, -12.5)):
    """Test RCNBNB"""
    pass

if __name__ == '__main__':
    unittest.main(verbosity=6)
