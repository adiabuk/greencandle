#pylint: disable=no-member,too-many-statements,too-many-locals

"""
Get/Convert Balances from Binance
"""

from collections import defaultdict
import requests
import cryptocompare
from str2bool import str2bool
from greencandle.lib.balance_common import default_to_regular, get_quote, get_base
from greencandle.lib.auth import binance_auth
from greencandle.lib.logger import get_logger
from greencandle.lib import config

config.create_config()
BITCOIN = {}
LOGGER = get_logger(__name__)

def get_local_price(pair):
    """
    Get current price of asset from local 5m stream
    """

    stream_req = requests.get(f"http://stream/5m/recent?pair={pair}", timeout=20)
    if 'GBP' in pair:
        client = binance_auth()
        return float(client.prices(pair)[pair])
    try:
        price = float(stream_req.json()['close'])
    except ValueError:
        client = binance_auth()
        price = float(client.prices(pair)[pair])
    return price

def get_max_borrow(pair):
    """
    Get max amount we can borrow based on direction and cross/isolated
    Return in asset amount and USD
    """
    client = binance_auth()
    asset = get_quote(pair) if config.main.trade_direction == 'long' else get_base(pair)
    max_borrow = client.get_max_borrow(asset=asset, isolated_pair=pair,
                                       isolated=str2bool(config.main.isolated))
    max_usd_borrow = max_borrow if 'USD' in asset else base2quote(max_borrow, asset+'USDT')
    return max_borrow, max_usd_borrow

def get_cross_assets_with_debt(debt_type='borrowed', amount=False):
    """
    get unique set of assets which have a loan against them
    Input: debt_type: borrowed|interest
           amount: True|False
    Output: if amount==True: string asset
            if amount==False: tupple (string asset,
                                      float borrowed|interest,
                                      float free)
    """
    client = binance_auth()
    cross_details = client.get_cross_margin_details()
    borrowed_set = set()

    # get unique set of assets which have a loan against tem
    for item in cross_details['userAssets']:
        if float(item[debt_type]) > 0:
            if amount:
                borrowed_set.add((item['asset'],
                                  float(item[debt_type]),
                                  float(item['free'])))
            else:
                borrowed_set.add(item['asset'])
    return borrowed_set

def get_cross_margin_level():
    """
    Calculate cross margin risk level
    risk = total_assets / total_debts
    """
    client = binance_auth()

    total_free = 0
    total_debt = 0
    details = [item for item in client.get_cross_margin_details()['userAssets']
               if item['netAsset'] != '0']
    for item in details:
        asset = item['asset']
        debt = float(item['borrowed']) + float(item['interest'])
        usd_debt = base2quote(debt, asset+'USDT') if 'USD' not in asset else debt
        free = item['free']
        usd_free = base2quote(free, asset+'USDT') if 'USD' not in asset else free
        total_free += float(usd_free)
        total_debt += float(usd_debt)
    try:
        return total_free / total_debt
    except ZeroDivisionError:
        return 999

def quote2base(amount, pair):
    """
    convert quote amount to base amount
    """
    price = get_local_price(pair)
    return float(amount) / price

def base2quote(amount, pair):
    """
    convert base amount to quote amount
    """
    price = get_local_price(pair)
    return float(amount) * price

def usd2gbp():
    """
    Get usd/gbp rate
    """
    price = get_local_price('GBPUSDT')
    return  1/price

def get_current_isolated():
    """Get balance for isolated accounts"""

    client = binance_auth()
    all_balances = client.isolated_balances()
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
    result["isolated"]["TOTALS"]["GBP"] = 0
    result["isolated"]["TOTALS"]["isolated"] = 0


    isolated = get_current_isolated()
    for key, val in isolated.items():
        current_quote = get_quote(key)
        for quote, amount in val.items():
            bcoin = 0
            usd = 0
            gbp = 0
            if quote == "BTC":
                bcoin = float(amount)
                usd = float(amount) / get_local_price('BTCUSDT')

            elif "USD" in quote:
                bcoin = float(amount) / get_local_price('BTCUSDT')
                usd = float(amount)

            elif quote == 'GBP':
                bcoin = float(amount) / get_local_price('BTCGBP')
                usd = bcoin / get_local_price('BTCUSDT')

            else:  # other currencies that need converting to USDT
                try:
                    LOGGER.debug("Converting currency %s", key)
                    bcoin = float(amount) * get_local_price(quote+'USDT')  # value in USDT
                    usd = float(bcoin) * get_local_price('BTCUSDT')
                except KeyError:
                    LOGGER.critical("Error: Unable to quantify isolated currency: %s", quote)
                    continue

            gbp = usd2gbp() * usd

            bitcoin_total += bcoin
            usd_total += usd
            gbp_total += gbp
            result["isolated"][key]["BTC"] = bcoin
            result["isolated"][key]["USD"] = usd
            result["isolated"][key]["GBP"] = gbp
            result["isolated"][key]["count"] = val[current_quote]
            result["isolated"][key][quote] = amount

    result["isolated"]["TOTALS"]["BTC"] = bitcoin_total
    result["isolated"]["TOTALS"]["USD"] = usd_total
    result["isolated"]["TOTALS"]["count"] = "N/A"
    gbp_total = usd2gbp() * usd_total
    result["isolated"]["TOTALS"]["GBP"] = gbp_total

    return default_to_regular(result)

def get_binance_cross():
    """Get totals for each crypto from binance and convert to USD/GBP"""

    mydict = lambda: defaultdict(mydict)
    result = mydict()
    result["margin"]["TOTALS"]["BTC"] = 0
    result["margin"]["TOTALS"]["USD"] = 0
    result["margin"]["TOTALS"]["GBP"] = 0
    result["margin"]["TOTALS"]["count"] = 0

    client = binance_auth()
    all_balances = client.margin_balances()
    bitcoin_totals = 0
    usd_totals = 0
    gbp_total = 0
    usd_total = 0

    for key in all_balances:
        LOGGER.debug('%s %s ', str(key), str(all_balances[key]["net"]))
        current_value = float(all_balances[key]["net"])
        current_gross = float(all_balances[key]["gross"])

        if float(current_value) != 0:  # available currency
            result["margin"][key]["count"] = current_value
            result["margin"][key]["gross_count"] = current_gross

            if key == "BTC":
                bcoin = float(current_value)
                bitcoin_totals += bcoin
                usd = bcoin * get_local_price('BTCUSDT')
                usd_totals += usd

            elif key in ("USDT", "LBUSD", "BUSD"):
                bcoin = float(current_value) / get_local_price('BTCUSDT')
                bitcoin_totals += bcoin
                usd_totals += bcoin * get_local_price('BTCUSDT')
                usd = current_value

            elif key == "GBP":
                bcoin = float(current_value) / get_local_price('BTCGBP')
                bitcoin_totals += bcoin
                usd_totals += bcoin * get_local_price('BTCUSDT')

            else:  # other currencies that need converting to USDT
                try:
                    LOGGER.debug("Converting currency %s", key)
                    usd = float(current_value) * get_local_price(key+'USDT')  # value in USDT
                    usd_totals += usd
                    bcoin = usd / get_local_price('BTCUSDT')
                    bitcoin_totals += bcoin

                except KeyError:
                    LOGGER.critical("Error: Unable to quantify cross currency: %s", key)
                    continue

            add_value(key, bcoin)

            gbp = usd2gbp() * usd
            usd_total += usd
            gbp_total += gbp
            result["margin"][key]["BTC"] = bcoin
            result["margin"][key]["USD"] = usd
            result["margin"][key]["GBP"] = gbp

    usd_total = bitcoin_totals * get_local_price('BTCUSDT')
    result["margin"]["TOTALS"]["BTC"] = bitcoin_totals
    result["margin"]["TOTALS"]["USD"] = usd_total
    result["margin"]["TOTALS"]["count"] = "N/A"
    gbp_total = usd2gbp() * usd_total
    result["margin"]["TOTALS"]["GBP"] = gbp_total
    add_value("USD", usd_total)
    add_value("GBP", gbp_total)

    return default_to_regular(result)

def get_binance_spot():
    """Get totals for each crypto from binance and convert to USD/GBP"""

    mydict = lambda: defaultdict(mydict)
    result = mydict()
    result["binance"]["TOTALS"]["BTC"] = 0
    result["binance"]["TOTALS"]["USD"] = 0
    result["binance"]["TOTALS"]["GBP"] = 0
    result["binance"]["TOTALS"]["count"] = 0

    client = binance_auth()
    balances = client.balances()
    all_balances = {k: v for k, v in balances.items()
                    if float(v['free']) > 0 or float(v['locked']) > 0}
    prices = client.prices()
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
            elif key in ("USDT", "LDBUSD", "BUSD"):  # LDBUSD is USD savings
                bcoin = float(current_value) / float(prices["BTCUSDT"])
                bitcoin_totals += bcoin
            elif key == "GBP":
                bcoin = float(current_value) / float(prices["BTCGBP"])
                bitcoin_totals += bcoin
            elif key == "TWT":
                bcoin = (float(current_value) * cryptocompare.get_price \
                        ('TWT', curr='USD')['TWT']['USD']) \
                        / float(prices["BTCUSDT"])
                bitcoin_totals += bcoin
            elif key == 'ETHW':
                LOGGER.debug("skipping coin: %s", key)
                continue

            else:  # other currencies that need converting to BTC
                try:
                    LOGGER.debug("Converting spot currency %s %s", key, str(current_value))
                    bcoin = float(current_value) * float(prices[key+"BTC"])  # value in BTC
                    bitcoin_totals += bcoin
                except KeyError:
                    LOGGER.critical("Error: Unable to quantify spot currency: %s ", key)
                    continue

            add_value(key, bcoin)

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
        result["binance"]["TOTALS"]["count"] = "N/A"
        gbp_total = usd2gbp() * usd_total
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
