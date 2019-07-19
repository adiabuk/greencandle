#!/usr/bin/env python
""" print pip values for all symbols in ascending order """

import os
import json
from coinbase.wallet.client import Client
from forex_python.converter import CurrencyRates
import binance

HOME_DIR = os.path.expanduser("~")
CONFIG = json.load(open(HOME_DIR + "/.coinbase"))
API_KEY = CONFIG["api_key"]
API_SECRET = CONFIG["api_secret"]

CURRENCY = CurrencyRates()
RATE = CURRENCY.get_rate("USD", "GBP")
CLIENT = Client(API_KEY, API_SECRET)
RATES = CLIENT.get_exchange_rates()["rates"]
PIPS = []

for key, value in binance.prices().items():
    quote = key[-3:]
    try:
        usd = 0.0001 * float(value) * 10000 * float(RATES[quote])
        gbp = usd * RATE
    except KeyError:
        continue
    PIPS.append([key, gbp])

PIPS.sort(key=lambda x: x[1])
for item in PIPS:
    print(item[0], "{0:.10f}".format(item[1]))
