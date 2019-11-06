#pylint: disable=unnecessary-pass

"""
Unittest file for testing results of a run using downloaded data
"""
import unittest
from .unittests import make_test_case

class TestBTCUSDT(make_test_case('BTCUSDT', '2019-05-05', 27, 11, -4.6)):
    """Test BTCUSDT"""
    pass

class TestBNBETH(make_test_case('BNBETH', '2019-02-27', 35, 14, -5.5)):
    """Test BNBETH"""
    pass

class TestLRCBTC(make_test_case('LRCBTC', '2019-01-08', 20, 12, -8)):
    """Test LRCBTC"""
    pass

class TestRCNBNB(make_test_case('RCNBNB', '2019-03-29', 24, 23, -5)):
    """Test RCNBNB"""
    pass

if __name__ == '__main__':
    unittest.main(verbosity=6)
