#pylint: disable=no-member,wrong-import-order,logging-not-lazy

"""
Get/Convert Balances from Binance
"""

from collections import defaultdict
from binance import binance
import cryptocompare
from forex_python.converter import CurrencyRates, RatesNotAvailableError
from .balance_common import default_to_regular
from .auth import binance_auth
from .logger import get_logger
from . import config
config.create_config()
BITCOIN = {}
LOGGER = get_logger(__name__)

CURRENCY = CurrencyRates()
#USD2GBP = lambda: CURRENCY.get_rate("USD", "GBP")

def get_current_isolated():
    """Get balance for isolated accounts"""
    for account in config.accounts.binance:
        binance_auth(account)
    all_balances = binance.isolated_balances()
    return all_balances

def get_binance_isolated():
    """
    Get totals for each crypto in each symbol  from binance isolated account
    and convert to USD/GBP
    """

    mydict = lambda: defaultdict(mydict)
    result = mydict()
    bitcoin_total = 0
    gbp_total = 0
    usd_total = 0
    result["isolated"]["TOTALS"]["BTC"] = 0
    result["isolated"]["TOTALS"]["USD"] = 0


    isolated = get_current_isolated()
    prices = binance.prices()
    for key, val in isolated.items():
        for base, amount in val.items():
            bcoin = 0
            usd = 0
            gbp = 0
            if base == "BTC":
                bcoin = float(amount)

            elif base == "USDT":
                bcoin = float(amount) / float(prices["BTCUSDT"])

            else:  # other currencies that need converting to BTC
                try:
                    LOGGER.debug("Converting currency %s" % key)
                    bcoin = float(amount) * float(prices[base+"BTC"])  # value in BTC
                except KeyError:
                    LOGGER.critical("Error: Unable to quantify margin currency: %s" % base)
                    continue

            usd = bcoin*float(prices['BTCUSDT'])
            #gbp = USD2GBP() * usd
            gbp = 1.41 * usd # FIXME

            bitcoin_total += bcoin
            usd_total += usd
            gbp_total += gbp
            result["isolated"][key]["BTC"] = bcoin
            result["isolated"][key]["USD"] = usd
            result["isolated"][key]["GBP"] = gbp
            result["isolated"][key]["count"] = "N/A"

    result["isolated"]["TOTALS"]["BTC"] = bitcoin_total
    result["isolated"]["TOTALS"]["USD"] = usd_total
    result["isolated"]["TOTALS"]["count"] = "N/A"
    for _ in range(3):
        # Try to get exchange rate 3 times before giving up
        try:
            #gbp_total = USD2GBP() * usd_total
            gbp_total = 1.41 * usd_total
        except RatesNotAvailableError:
            continue
        break
    result["isolated"]["TOTALS"]["GBP"] = gbp_total

    return default_to_regular(result)

def get_binance_margin():
    """Get totals for each crypto from binance and convert to USD/GBP"""

    mydict = lambda: defaultdict(mydict)
    result = mydict()
    result["margin"]["TOTALS"]["BTC"] = 0
    result["margin"]["TOTALS"]["USD"] = 0
    for account in config.accounts.binance:

        binance_auth(account)
        all_balances = binance.margin_balances()
        prices = binance.prices()
        bitcoin_totals = 0
        gbp_total = 0
        usd_total = 0

        for key in all_balances:
            LOGGER.debug('%s %s ' % (str(key), str(all_balances[key]["net"])))
            current_value = float(all_balances[key]["net"])

            if float(current_value) != 0:  # available currency
                result["margin"][key]["count"] = current_value

                if key == "BTC":
                    bcoin = float(current_value)
                    bitcoin_totals += float(bcoin)

                elif key == "USDT":
                    bcoin = float(current_value) / float(prices["BTCUSDT"])
                    bitcoin_totals += bcoin

                else:  # other currencies that need converting to BTC
                    try:
                        LOGGER.debug("Converting currency %s" % key)
                        bcoin = float(current_value) * float(prices[key+"BTC"])  # value in BTC
                        bitcoin_totals += bcoin
                    except KeyError:
                        LOGGER.critical("Error: Unable to quantify margin currency: %s" % key)
                        continue

                add_value(key, bcoin)

                usd = bcoin *float(prices["BTCUSDT"])
                #gbp = USD2GBP() * usd
                gbp = 1.41 * usd
                usd_total += usd
                gbp_total += gbp
                result["margin"][key]["BTC"] = bcoin
                result["margin"][key]["USD"] = usd
                result["margin"][key]["GBP"] = gbp

        usd_total = bitcoin_totals * float(prices["BTCUSDT"])
        result["margin"]["TOTALS"]["BTC"] += bitcoin_totals
        result["margin"]["TOTALS"]["USD"] += usd_total
        result["margin"]["TOTALS"]["count"] = "N/A"
        for _ in range(3):
            # Try to get exchange rate 3 times before giving up
            try:
                #gbp_total = USD2GBP() * usd_total
                gbp_total = 1.41 * usd_total #FIXME
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
    result["binance"]["TOTALS"]["BTC"] = 0
    result["binance"]["TOTALS"]["USD"] = 0

    for account in config.accounts.binance:

        binance_auth(account)
        all_balances = binance.balances()
        prices = binance.prices()
        bitcoin_totals = 0
        gbp_total = 0
        usd_total = 0

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
                elif key == "TWT":
                    bcoin = (float(current_value) * cryptocompare.get_price \
                            ('TWT', curr='USD')['TWT']['USD']) \
                            / float(prices["BTCUSDT"])
                    bitcoin_totals += bcoin

                else:  # other currencies that need converting to BTC
                    try:
                        LOGGER.debug("Converting spot currency %s %s" % (key, str(current_value)))
                        bcoin = float(current_value) * float(prices[key+"BTC"])  # value in BTC
                        bitcoin_totals += bcoin
                    except KeyError:
                        LOGGER.critical("Error: Unable to spot quantify currency: %s " % key)
                        continue

                add_value(key, bcoin)

                usd = bcoin *float(prices["BTCUSDT"])
                #gbp = USD2GBP() * usd
                gbp = 1.41 * usd # FIXME
                usd_total += usd
                gbp_total += gbp
                result["binance"][key]["BTC"] = bcoin
                result["binance"][key]["USD"] = usd
                result["binance"][key]["GBP"] = gbp

        usd_total = bitcoin_totals * float(prices["BTCUSDT"])
        result["binance"]["TOTALS"]["BTC"] += bitcoin_totals
        result["binance"]["TOTALS"]["USD"] += usd_total
        result["binance"]["TOTALS"]["count"] = "N/A"
        for _ in range(3):
            # Try to get exchange rate 3 times before giving up
            try:
                #gbp_total = USD2GBP() * usd_total
                gbp_total = 1.41 * usd_total # FIXME
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
