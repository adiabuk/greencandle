#pylint: disable=no-member,wrong-import-order
"""
Helper functions for authernticating with APIs
"""

import os
from binance.binance import Binance
from coinbase.wallet.client import Client
import ccxt
from greencandle.lib import config

HOME_DIR = os.path.expanduser("~")

def binance_auth(test=False):
    """
    Authenticatate with binance API using credentials in config
    """
    config.create_config()
    account = config.accounts.binance[0]
    client = Binance(api_key=account['key'],
                     secret=account['secret'],
                     test=test)
    return client

def coinbase_auth(account):
    """
    Authenticatate with coinbase API using credentials in config
    Returns: Coinbase authenticated client object
    """

    api_key = account['key']
    api_secret = account['secret']

    client = Client(api_key, api_secret)
    return client

def phemex_auth(acct_type, account):
    """
    Authenticatate with API using key/secret
    Returns: Coinbase phemex client object
    """

    api_key = account['key']
    api_secret = account['secret']

    exchange = ccxt.phemex({
        'enableRateLimit': True,  # https://github.com/ccxt/ccxt/wiki/Manual#rate-limit
        'apiKey': api_key,  # testnet keys if using the testnet sandbox
        'secret': api_secret,  # testnet keys if using the testnet sandbox
        'options': {
            'defaultType': acct_type,
        },
    })

    return exchange
