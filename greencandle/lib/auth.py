#pylint: disable=no-member
"""
Helper functions for authernticating with APIs
"""

import os
from coinbase.wallet.client import Client
import ccxt
import binance
from . import config

HOME_DIR = os.path.expanduser("~")

def binance_auth(account):
    """
    Authenticatate with binance API using credentials in $HOME/.binance
    """

    api_key = account['key']
    api_secret = account['secret']
    binance.set(api_key, api_secret)

def coinbase_auth(account):
    """
    Authenticatate with coinbase API using credentials in $HOME/.coinbase
    Returns: Coinbase authenticated client object
    """

    api_key = account['key']
    api_secret = account['secret']

    client = Client(api_key, api_secret)
    return client

def phemex_auth(type, account):
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
            'defaultType': type,
        },
    })

    return exchange
