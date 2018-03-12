"""
Common functions that don't belong anywhere else
"""

import numpy

def make_float(arr):
    """Convert dataframe array into float array"""
    return numpy.array([float(x) for x in arr.values])
