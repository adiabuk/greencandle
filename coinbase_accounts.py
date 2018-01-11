#!/usr/bin/env python

"""Get account details from coinbase"""

import json
import os
from coinbase.wallet.client import Client

HOME_DIR = os.path.expanduser('~')
CONFIG = json.load(open(HOME_DIR + '/.coinbase'))
API_KEY = CONFIG['api_key']
API_SECRET = CONFIG['api_secret']

CLIENT = Client(API_KEY, API_SECRET)

print CLIENT.get_accounts()
