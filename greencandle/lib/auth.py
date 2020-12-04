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

def binance_auth():
    """
    Authenticatate with binance API using credentials in $HOME/.binance
    """

    api_key = config.main.binance_api_key
    api_secret = config.main.binance_api_secret
    binance.set(api_key, api_secret)

def coinbase_auth():
    """
    Authenticatate with coinbase API using credentials in $HOME/.coinbase
    Returns: Coinbase authenticated client object
    """

    api_key = config.main.coinbase_api_key
    api_secret = config.main.coinbase_api_secret

    client = Client(api_key, api_secret)
    return client

def phemex_auth(account):
    """
    Authenticatate with API using key/secret
    Returns: Coinbase phemex client object
    """

    api_key = config.main.phemex_api_key
    api_secret = config.main.phemex_api_secret

    exchange = ccxt.phemex({
        'enableRateLimit': True,  # https://github.com/ccxt/ccxt/wiki/Manual#rate-limit
        'apiKey': api_key,  # testnet keys if using the testnet sandbox
        'secret': api_secret,  # testnet keys if using the testnet sandbox
        'options': {
            'defaultType': account,
        },
    })

    return exchange
