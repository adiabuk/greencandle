#!/usr/bin/env python

"""Get account value from binance and coinbase """

from __future__ import print_function
import json

from requests.exceptions import ReadTimeout
from lib.binance_accounts import get_binance_values
from lib.coinbase_accounts import get_coinbase_values
from lib.mysql import insert_balance

def get_balance():
    """get dict of all balances """

    binance = get_binance_values()
    try:
        coinbase = get_coinbase_values()
    except ReadTimeout:
        print("Unable to get coinbase balance")
        coinbase = {}
    combined_dict = binance.copy()   # start with binance's keys and values
    combined_dict.update(coinbase)    # modifies z with y's keys and values & returns None

    insert_balance(combined_dict)
    return combined_dict

def main():
    """print formated json of dict when called directly """
    print(json.dumps(get_balance(), indent=4))

if __name__ == "__main__":
    main()
