#!/usr/bin/env python
"""
Print exchange rates
"""

import sys
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import arg_decorator

@arg_decorator
def main():
    """
    Get USD/GBP exchange rates for given quote
    """
    mysql = Mysql()
    quote = sys.argv[1]
    rates = mysql.get_rates(quote)
    print("USD: {}, GBP: {}".format(rates[0], rates[1]))

if __name__ == '__main__':
    main()
