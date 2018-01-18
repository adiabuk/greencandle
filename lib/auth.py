"""
Helper functions for authernticating with APIs
"""

import os
import json
from coinbase.wallet.client import Client
import binance

HOME_DIR = os.path.expanduser('~')

def binance_auth():
    """
    Authenticatate with binance API using credentials in $HOME/.binance
    """

    config = json.load(open(HOME_DIR + '/.binance'))
    api_key = config['api_key']
    api_secret = config['api_secret']
    binance.set(api_key, api_secret)

def coinbase_auth():
    """
    Authenticatate with coinbase API using credentials in $HOME/.coinbase
    """

    config = json.load(open(HOME_DIR + '/.coinbase'))
    api_key = config['api_key']
    api_secret = config['api_secret']
    client = Client(api_key, api_secret)
    return client
