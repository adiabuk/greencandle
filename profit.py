#!/usr/bin/env python

from forex_python.converter import CurrencyRates
import binance

CURRENCY = CurrencyRates()
def get_profit(pair, buy_price, sell_price):
    """
    eg.  pair=OMGETH
    base = OMG
    QUOTE=ETH
    QUOTE/HOME = ETH/GBP
    """

    base = pair[:-3]
    quote = pair[-3:]
    home = "GBP"
    intermed = "USD"
    quotehome = binance.prices()[quote + 'USDT'] * CURRENCY.get_rate(intermed, home)
    formula = float(sell_price) - float(buy_price) * quotehome
    #number_of_units = 50gbp => base
    print(formula)


def gbp_to_base(gbp, symbol):
    """
    50GBP => OMG
      50GBP => USD
      USD => BTC
      BTC => OMG
    """

    usd = gbp * CURRENCY.get_rate('GBP', 'USD')
    btc = usd * float(binance.prices()['BTCUSDT'])
    omg = btc * float(binance.prices()[symbol + "BTC"])
    return "{0:.10f}".format(omg)

if __name__ == "__main__":
    print(gbp_to_base(50, "OMG"))
