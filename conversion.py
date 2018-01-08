#!/usr/bin/env python
import requests


SUPPORTED_CURRENCIES = {
    "EUR": "European euro",
    "USD": "US dollar",
    "GBP": "Pound sterling",
    "BRL": "Brazilian real"
}


CURRENCY_CODES = {
    1: "EUR",
    2: "USD",
    3: "GBP",
    4: "BRL"
}


def get_exchange_rate(base_currency, target_currency):
    if not (base_currency in SUPPORTED_CURRENCIES.keys()):
        raise ValueError("base currency {} not supported".format(base_currency))
    if not (target_currency in SUPPORTED_CURRENCIES.keys()):
        raise ValueError("target currency {} not supported".format(target_currency))

    if base_currency == target_currency:
        return 1

    api_uri = "https://api.fixer.io/latest?base={}&symbols={}".format(base_currency, target_currency)
    api_response = requests.get(api_uri)

    if api_response.status_code == 200:
        return api_response.json()["rates"][target_currency]

print get_exchange_rate('GBP', 'USD')
