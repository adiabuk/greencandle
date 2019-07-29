"""
Helper functions for authernticating with APIs
"""

import os
from coinbase.wallet.client import Client
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
