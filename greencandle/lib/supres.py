#!/usr/bin/env python

"""
find support/resistance levels
Adapted from:
https://kite.trade/forum/discussion/1047/a-simple-python-function-to-detect-support-resistance-levels
"""

import numpy as np
from scipy.signal import savgol_filter as smooth

def supres(ltp, num):
    """
    This function takes a numpy array of last traded price
    and returns a list of support and resistance levels
    respectively. num is the number of entries to be scanned.
    """

    #converting n to a nearest even number
    if num%2 != 0:
        num += 1

    n_ltp = ltp.shape[0]

    # smoothening the curve
    ltp_s = smooth(ltp, (num + 1), 3)

    #taking a simple derivative
    ltp_d = np.zeros(n_ltp)
    ltp_d[1:] = np.subtract(ltp_s[1:], ltp_s[:-1])

    resistance = []
    support = []

    for i in range(n_ltp - num):
        arr_sl = ltp_d[i:(i + num)]
        first = arr_sl[:int(num / 2)] #first half
        last = arr_sl[int(num / 2):] #second half

        r_1 = np.sum(first > 0)
        r_2 = np.sum(last < 0)

        s_1 = np.sum(first < 0)
        s_2 = np.sum(last > 0)

        #local maxima detection
        if (r_1 == (num / 2)) and (r_2 == (num / 2)):
            resistance.append(ltp[int(i+((num / 2)-1))])

        #local minima detection
        if (s_1 == (num / 2)) and (s_2 == (num / 2)):
            support.append(ltp[int(i+((num / 2)-1))])

    return support, resistance
