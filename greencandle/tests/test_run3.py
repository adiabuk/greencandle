#pylint: disable=unnecessary-pass,too-few-public-methods

"""
Unittest file for testing results of a run using downloaded data
"""
import unittest
from .unittests import make_test_case

class TestBNBETH(make_test_case('unit/cross', 'BNBETH', '1h', '2019-02-27', 15, 35, 14, -5.5,
                                61, 9.2)):
    """
    Test BNBETH
    cross margin long divisor=2
    """

    pass

class TestBNBETH(make_test_case('unit/isolated-long', 'BNBETH', '1h', '2019-02-27', 15, 35, 14, -5.5,
                                61, 9.2)):
    """
    Test BNBETH
    cross margin long divisor=2
    """

    pass


if __name__ == '__main__':
    unittest.main(verbosity=6)
