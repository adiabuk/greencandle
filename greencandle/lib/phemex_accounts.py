#pylint: disable=no-member,too-many-locals,unsubscriptable-object

"""
Get/Convert Balances from Phemex
"""

from collections import defaultdict
from currency_converter import CurrencyConverter
import ccxt
from greencandle.lib.balance_common import default_to_regular
from greencandle.lib.auth import phemex_auth
from greencandle.lib.logger import get_logger
from greencandle.lib import config
config.create_config()
BITCOIN = {}
LOGGER = get_logger(__name__)

def get_phemex_values():
    """Get totals for each crypto from binance and convert to USD/GBP"""
    currency = CurrencyConverter()

    mydict = lambda: defaultdict(mydict)
    result = mydict()
    result["phemex"]["TOTALS"]["BTC"] = 0
    result["phemex"]["TOTALS"]["USD"] = 0
    result["phemex"]["TOTALS"]["GBP"] = 0

    for account in config.accounts.phemex:
        hitbtc = ccxt.hitbtc()

        # Get spot account details
        phemex = phemex_auth('spot', account)
        balance = phemex.fetch_balance({'code':'BTC'})
        spot_total = balance['total']['USDT']
        for key, val in balance['total'].items():
            LOGGER.debug("Getting phemex %s", key)
            # iterate through all items and convert to USDT
            if val > 0 and key != 'USDT':
                ticker = hitbtc.fetch_ticker(f'{key}/USDT')['close']
                spot_total += val * ticker


        # Get margin account details
        phemex = phemex_auth('swap', account)
        usd2gbp = currency.convert(1, 'USD', 'GBP')
        btc = phemex.fetch_balance({'code': 'BTC'})['total']['BTC']

        # add spot usdt to usd
        usd = phemex.fetch_balance({'code': 'USD'})['total']['USD'] + spot_total

        bitcoin_ticker = hitbtc.fetch_ticker('BTC/USDT')
        price = bitcoin_ticker['close']
        gbp = (btc*price) * usd2gbp

        result["phemex"]["BTC"] = {}
        result["phemex"]["BTC"]["count"] = btc
        result["phemex"]["BTC"]["BTC"] = btc
        result["phemex"]["BTC"]["USD"] = btc * price
        result["phemex"]["BTC"]["GBP"] = gbp

        result["phemex"]["USD"] = {}
        result["phemex"]["USD"]["USD"] = usd
        result["phemex"]["USD"]["count"] = usd
        result["phemex"]["USD"]["BTC"] = usd / price
        result["phemex"]["USD"]["GBP"] = usd  * usd2gbp

        btc_total = btc + (usd/price)
        usd_total = btc_total * price
        result["phemex"]["TOTALS"]["BTC"] += btc_total
        result["phemex"]["TOTALS"]["USD"] += usd_total
        result["phemex"]["TOTALS"]["count"] = "N/A"
        result["phemex"]["TOTALS"]["GBP"] += usd_total * usd2gbp



        #usd = bcoin *float(prices["BTCUSDT"])
        gbp = usd2gbp * usd_total

    return default_to_regular(result)
