#pylint: disable=no-member

"""Get account details from coinbase"""

from __future__ import print_function
import json
from collections import defaultdict
from requests.exceptions import ReadTimeout
from forex_python.converter import CurrencyRates
from .balance_common import default_to_regular
from .auth import coinbase_auth
from .timeout import restrict_timeout
from . import config
config.create_config()

def get_coinbase_values():
    """Get totals for each crypto from binance and convert to USD/GBP"""
    mydict = lambda: defaultdict(mydict)
    result = mydict()
    result["coinbase"]["TOTALS"]["BTC"] = 0
    result["coinbase"]["TOTALS"]["USD"] = 0
    result["coinbase"]["TOTALS"]["GBP"] = 0

    for account in config.accounts.coinbase:

        client = coinbase_auth(account)
        currency = CurrencyRates()
        all_accounts = {}
        with restrict_timeout(5, name="coinbase accounts"):  # allow to run for only 5 seconds
            all_accounts = client.get_accounts()
        if not all_accounts:
            raise ReadTimeout

        json_accounts = json.loads(str(all_accounts))
        gbp_totals = 0
        usd_totals = 0
        btc_totals = 0
        rates = client.get_exchange_rates()["rates"]
        for data in json_accounts["data"]:
            if "0.00" not in data["balance"]["amount"]:  #if account has a balance
                current_count = data["balance"]["amount"]  # count of current currency
                result["coinbase"][data["currency"]]["count"] = current_count

                # amount in GBP
                current_gbp = data["native_balance"]["amount"]
                gbp_totals += float(current_gbp)
                result["coinbase"][data["currency"]]["GBP"] = current_gbp

                # amount in USD
                current_usd = float(currency.get_rate("GBP", "USD")) * float(current_gbp)
                usd_totals += float(current_usd)
                result["coinbase"][data["currency"]]["USD"] = current_usd

                # amount in BTC
                current_btc = current_count if data["currency"] == "BTC" else \
                        float(current_usd) * float(rates["BTC"]) # USD -> BTC
                btc_totals += float(current_btc)
                result["coinbase"][data["currency"]]["BTC"] = current_btc


                result["coinbase"]["TOTALS"]["BTC"] += btc_totals
                result["coinbase"]["TOTALS"]["USD"] += usd_totals
                result["coinbase"]["TOTALS"]["GBP"] += gbp_totals
                result["coinbase"]["TOTALS"]["count"] = ""

    return default_to_regular(result)

if __name__ == "__main__":
    print(get_coinbase_values())
