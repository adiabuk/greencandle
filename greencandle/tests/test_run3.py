#pylint: disable=unnecessary-pass,too-few-public-methods

"""
Unittest file for testing results of a run using downloaded data
Rules for short have not been revered from long
"""
import unittest
from .unittests import make_test_case

class TestBNBETHCrossLong(make_test_case('unit/cross', 'BNBETH', '1h', '2019-02-27',
                                         15, 35, 14, -5.5, 61, 9.2)):
    """
    Test BNBETH
    cross margin long divisor=2
    """

    pass

class TestBNBETHIsoLong(make_test_case('unit/isolated-long', 'BNBETH', '1h', '2019-02-27',
                                       15, 35, 14, -5.5, 61, 9.2)):
    """
    Test BNBETH
    isolated margin long divisor=2
    """

    pass

class TestBNBETHIsoShort(make_test_case('unit/isolated-short', 'BNBETH', '1h',
                                        '2019-02-27', 15, -46, 3, -21, 13.8, 9.2)):
    """
    Test BNBETH
    isolated margin short divisor=2
    """

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
