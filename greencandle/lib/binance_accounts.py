#pylint: disable=no-member,wrong-import-order

"""
Get/Convert Balances from Binance
"""

from collections import defaultdict
import binance
from forex_python.converter import CurrencyRates, RatesNotAvailableError
from .balance_common import default_to_regular
from .auth import binance_auth
from .logger import get_logger
from . import config

BITCOIN = {}
LOGGER = get_logger(__name__)

def get_binance_margin():
    """Get totals for each crypto from binance and convert to USD/GBP"""

    mydict = lambda: defaultdict(mydict)
    result = mydict()
    binance_auth()
    all_balances = binance.margin_balances()
    prices = binance.prices()
    bitcoin_totals = 0
    gbp_total = 0
    usd_total = 0
    currency = CurrencyRates()

    for key in all_balances:
        current_value = float(all_balances[key]["net"])

        if float(current_value) > 0:  # available currency
            result["margin"][key]["count"] = current_value

            if key == "BTC":
                bcoin = float(current_value)
                bitcoin_totals += float(bcoin)

            elif key == "USDT":
                bcoin = float(current_value) / float(prices["BTCUSDT"])
                bitcoin_totals += bcoin

            else:  # other currencies that need converting to BTC
                try:
                    bcoin = float(current_value) * float(prices[key+"BTC"])  # value in BTC
                    bitcoin_totals += bcoin
                except KeyError:
                    LOGGER.critical("Error: Unable to quantify currency: %s ", key)
                    continue

            add_value(key, bcoin)
            usd2gbp = lambda: currency.get_rate("USD", "GBP")

            usd = bcoin *float(prices["BTCUSDT"])
            gbp = usd2gbp() * usd
            usd_total += usd
            gbp_total += gbp
            result["margin"][key]["BTC"] = bcoin
            result["margin"][key]["USD"] = usd
            result["margin"][key]["GBP"] = gbp

    usd_total = bitcoin_totals * float(prices["BTCUSDT"])
    result["margin"]["TOTALS"]["BTC"] = bitcoin_totals
    result["margin"]["TOTALS"]["USD"] = usd_total
    result["margin"]["TOTALS"]["count"] = ""
    for _ in range(3):
        # Try to get exchange rate 3 times before giving up
        try:
            gbp_total = currency.get_rate("USD", "GBP") * usd_total
        except RatesNotAvailableError:
            continue
        break
    result["margin"]["TOTALS"]["GBP"] = gbp_total
    add_value("USD", usd_total)
    add_value("GBP", gbp_total)

    return default_to_regular(result)

def get_binance_values():
    """Get totals for each crypto from binance and convert to USD/GBP"""

    mydict = lambda: defaultdict(mydict)
    result = mydict()
    binance_auth()
    all_balances = binance.balances()
    prices = binance.prices()
    bitcoin_totals = 0
    gbp_total = 0
    usd_total = 0
    currency = CurrencyRates()

    for key in all_balances:
        current_value = float(all_balances[key]["free"]) + float(all_balances[key]["locked"])

        if float(current_value) > 0:  # available currency
            result["binance"][key]["count"] = current_value

            if key == "BTC":
                bcoin = float(current_value)
                bitcoin_totals += float(bcoin)

            elif key == "USDT":
                bcoin = float(current_value) / float(prices["BTCUSDT"])
                bitcoin_totals += bcoin

            else:  # other currencies that need converting to BTC
                try:
                    bcoin = float(current_value) * float(prices[key+"BTC"])  # value in BTC
                    bitcoin_totals += bcoin
                except KeyError:
                    LOGGER.critical("Error: Unable to quantify currency: %s ", key)
                    continue

            add_value(key, bcoin)
            usd2gbp = lambda: currency.get_rate("USD", "GBP")

            usd = bcoin *float(prices["BTCUSDT"])
            gbp = usd2gbp() * usd
            usd_total += usd
            gbp_total += gbp
            result["binance"][key]["BTC"] = bcoin
            result["binance"][key]["USD"] = usd
            result["binance"][key]["GBP"] = gbp

    usd_total = bitcoin_totals * float(prices["BTCUSDT"])
    result["binance"]["TOTALS"]["BTC"] = bitcoin_totals
    result["binance"]["TOTALS"]["USD"] = usd_total
    result["binance"]["TOTALS"]["count"] = ""
    for _ in range(3):
        # Try to get exchange rate 3 times before giving up
        try:
            gbp_total = currency.get_rate("USD", "GBP") * usd_total
        except RatesNotAvailableError:
            continue
        break
    result["binance"]["TOTALS"]["GBP"] = gbp_total
    add_value("USD", usd_total)
    add_value("GBP", gbp_total)

    return default_to_regular(result)

def add_value(key, value):
    """Add value to dict to save offline """
    try:
        BITCOIN[key].append(value)
    except KeyError:
        BITCOIN[key] = []
        BITCOIN[key].append(value)
