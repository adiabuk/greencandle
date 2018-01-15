#!/usr/bin/env python

"""Get account value from binance and coinbase """

import json
from binance_accounts import get_binance_values
from coinbase_accounts import get_coinbase_values

def get_balance():
    """get dict of all balances """

    binance = get_binance_values()
    coinbase = get_coinbase_values()
    combined_dict = binance.copy()   # start with x's keys and values
    combined_dict.update(coinbase)    # modifies z with y's keys and values & returns None

    return combined_dict

def main():
    """print formated json of dict when called directly """
    print(json.dumps(get_balance(), indent=4))

if __name__ == "__main__":
    main()
