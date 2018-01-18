#!/usr/bin/env python

"""
find support/resistance levels
Taken from:
https://kite.trade/forum/discussion/1047/a-simple-python-function-to-detect-support-resistance-levels
"""

import numpy as np
import pandas
from scipy.signal import savgol_filter as smooth
import binance
from klines import make_float

def supres(ltp, n):
    """
    This function takes a numpy array of last traded price
    and returns a list of support and resistance levels
    respectively. n is the number of entries to be scanned.
    """

    #converting n to a nearest even number
    if n%2 != 0:
        n += 1

    n_ltp = ltp.shape[0]

    # smoothening the curve
    ltp_s = smooth(ltp, (n+1), 3)

    #taking a simple derivative
    ltp_d = np.zeros(n_ltp)
    ltp_d[1:] = np.subtract(ltp_s[1:], ltp_s[:-1])

    resistance = []
    support = []

    for i in range(n_ltp - n):
        arr_sl = ltp_d[i:(i+n)]
        first = arr_sl[:int(n/2)] #first half
        last = arr_sl[int(n/2):] #second half

        r_1 = np.sum(first > 0)
        r_2 = np.sum(last < 0)

        s_1 = np.sum(first < 0)
        s_2 = np.sum(last > 0)

        #local maxima detection
        if (r_1 == (n/2)) and (r_2 == (n/2)):
            resistance.append(ltp[int(i+((n/2)-1))])

        #local minima detection
        if (s_1 == (n/2)) and (s_2 == (n/2)):
            support.append(ltp[int(i+((n/2)-1))])

    return support, resistance


def main():
    raw = binance.klines("XRPETH", "5m")
    print(len(raw))
    dataframe = pandas.DataFrame.from_dict(raw)
    close_values = make_float(dataframe.close)
    support, resistance = supres(close_values, 10)
    print("resistance:",resistance)
    print("current:", binance.prices()["XRPETH"])
    print("support:", support)

if __name__ == '__main__':
    main()
