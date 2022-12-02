#pylint: disable=unnecessary-pass,too-few-public-methods

"""
Unittest file for testing results of a run using downloaded data
"""
import unittest
from .unittests import make_test_case

class TestBNBETH(make_test_case('unit', 'BNBETH', '1h', '2019-02-27', 15, 35, 14, -5.5,
                                61, 9.2)):
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

class TestBNBETHCrossShort(make_test_case('unit/cross-short', 'BNBETH', '1h',
                                          '2019-02-27', 15, -46, 3, -21, 13.8, 9.2)):
    """
    Test BNBETH
    cross margin short divisor=2
    """

    pass

if __name__ == '__main__':
    unittest.main(verbosity=6)
