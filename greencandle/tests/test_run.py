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

class TestLRCBTC(make_test_case('LRCBTC', '2019-01-08', 50, 50, -5.5)):
    """Test LRCBTC"""
    pass

class TestRCNBNB(make_test_case('RCNBNB', '2019-03-29', 18, 10, -12.5)):
    """Test RCNBNB"""
    pass

if __name__ == '__main__':
    unittest.main(verbosity=6)
