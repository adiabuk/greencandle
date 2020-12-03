#pylint: disable=no-member,wrong-import-order

"""
Get/Convert Balances from Phemex
"""

from collections import defaultdict
from forex_python.converter import CurrencyRates
from .balance_common import default_to_regular
from .auth import phemex_auth
from .logger import get_logger
import ccxt

BITCOIN = {}
LOGGER = get_logger(__name__)

def get_phemex_values():
    """Get totals for each crypto from binance and convert to USD/GBP"""
    phemex = phemex_auth()
    currency = CurrencyRates()
    usd2gbp = lambda: currency.get_rate("USD", "GBP")
    btc = phemex.fetch_balance({'code': 'BTC'})['total']['BTC']
    usd = phemex.fetch_balance({'code': 'USD'})['total']['USD']

    mydict = lambda: defaultdict(mydict)
    result = mydict()
    hitbtc = ccxt.hitbtc()
    bitcoin_ticker = hitbtc.fetch_ticker('BTC/USDT')
    price = bitcoin_ticker['close']
    gbp = (btc*price) * usd2gbp()

    result["phemex"]["BTC"] = {}
    result["phemex"]["BTC"]["count"] = btc
    result["phemex"]["BTC"]["BTC"] = btc
    result["phemex"]["BTC"]["USD"] = btc * price
    result["phemex"]["BTC"]["GBP"] = gbp

    result["phemex"]["USD"] = {}
    result["phemex"]["USD"]["USD"] = usd
    result["phemex"]["USD"]["count"] = usd
    result["phemex"]["USD"]["BTC"] = usd / price
    result["phemex"]["USD"]["GBP"] = usd  * usd2gbp()

    btc_total = btc + (usd/price)
    usd_total = btc_total * price
    result["phemex"]["TOTALS"]["BTC"] = btc_total
    result["phemex"]["TOTALS"]["USD"] = usd_total
    result["phemex"]["TOTALS"]["count"] = ""
    result["phemex"]["TOTALS"]["GBP"] = usd_total * usd2gbp()



    #usd = bcoin *float(prices["BTCUSDT"])
    gbp = usd2gbp() * usd_total

    return default_to_regular(result)

def add_value(key, value):
    """Add value to dict to save offline """
    try:
        BITCOIN[key].append(value)
    except KeyError:
        BITCOIN[key] = []
        BITCOIN[key].append(value)
