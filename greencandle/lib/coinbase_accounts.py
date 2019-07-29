#!/usr/bin/env python

"""Get account details from coinbase"""

from __future__ import print_function
import json
from collections import defaultdict
from forex_python.converter import CurrencyRates
from requests.exceptions import ReadTimeout
from .balance_common import default_to_regular
from .auth import coinbase_auth
from .timeout import restrict_timeout
from . import config

CLIENT = coinbase_auth()

def get_coinbase_values():
    """Get totals for each crypto from binance and convert to USD/GBP"""

    mydict = lambda: defaultdict(mydict)
    result = mydict()
    currency = CurrencyRates()
    all_accounts = {}
    with restrict_timeout(5, name="coinbase accounts"):  # allow to run for only 5 seconds
        all_accounts = CLIENT.get_accounts()
    if not all_accounts:
        raise ReadTimeout

    json_accounts = json.loads(str(all_accounts))
    gbp_totals = 0
    usd_totals = 0
    btc_totals = 0
    rates = CLIENT.get_exchange_rates()["rates"]
    for account in json_accounts["data"]:
        if "0.00" not in account["balance"]["amount"]:  #if account has a balance
            current_count = account["balance"]["amount"]  # count of current currency
            result["coinbase"][account["currency"]]["count"] = current_count

            # amount in GBP
            current_gbp = account["native_balance"]["amount"]
            gbp_totals += float(current_gbp)
            result["coinbase"][account["currency"]]["GBP"] = current_gbp

            # amount in USD
            current_usd = float(currency.get_rate("GBP", "USD")) * float(current_gbp)
            usd_totals += float(current_usd)
            result["coinbase"][account["currency"]]["USD"] = current_usd

            # amount in BTC
            current_btc = current_count if account["currency"] == "BTC" else \
                    float(current_usd) * float(rates["BTC"]) # USD -> BTC
            btc_totals += float(current_btc)
            result["coinbase"][account["currency"]]["BTC"] = current_btc


            result["coinbase"]["TOTALS"]["BTC"] = btc_totals
            result["coinbase"]["TOTALS"]["USD"] = usd_totals
            result["coinbase"]["TOTALS"]["GBP"] = gbp_totals
            result["coinbase"]["TOTALS"]["count"] = ""

    #print json.dumps(json_accounts["data"][3])

    return default_to_regular(result)

if __name__ == "__main__":
    print(get_coinbase_values())
