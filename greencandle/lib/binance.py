#pylint: disable=unnecessary-comprehension,no-else-return
"""
Spot and margin trading module for binance
"""

import random
import hmac
import hashlib
import time
import inspect
from urllib.parse import urlencode
from urllib3.util.retry import Retry
import requests
from requests.adapters import HTTPAdapter

class Binance():
    """
    Provide methods for interacting with binance API
    """

    def __init__(self, api_key=None, secret=None, endpoint="",
                 debug=False):
        self.endpoint = endpoint if endpoint else random.choice(["https://api.binance.com",
                                                                 "https://api1.binance.com",
                                                                 "https://api2.binance.com",
                                                                 "https://api3.binance.com"])
        self.buy = "BUY"
        self.sell = "SELL"
        self.limit = "LIMIT"
        self.market = "MARKET"
        self.options = {"apiKey":api_key, "secret":secret}
        self.debug = debug

    def prices(self):
        """Get latest prices for all symbols."""
        data = self.request("GET", "/api/v1/ticker/allPrices")
        return {d["symbol"]: d["price"] for d in data}

    def tickers(self):
        """Get best price/qty on the order book for all symbols."""
        data = self.request("GET", "/api/v1/ticker/allBookTickers")
        return {d["symbol"]: {
            "bid": d["bidPrice"],
            "ask": d["askPrice"],
            "bidQty": d["bidQty"],
            "askQty": d["askQty"],
        } for d in data}

    def depth(self, symbol, **kwargs):
        """Get order book.

        Args:
            symbol (str)
            limit (int, optional): Default 100. Must be one of 50, 20, 100, 500, 5,
                200, 10.

        """
        params = {"symbol": symbol}
        params.update(kwargs)
        data = self.request("GET", "/api/v1/depth", params)
        return {
            "bids": {px: qty for px, qty, in data["bids"]},
            "asks": {px: qty for px, qty, in data["asks"]},
        }

    def klines(self, symbol, interval, **kwargs):
        """Get kline/candlestick bars for a symbol.

        Klines are uniquely identified by their open time. If startTime and endTime
        are not sent, the most recent klines are returned.

        Args:
            symbol (str)
            interval (str)
            limit (int, optional): Default 500; max 500.
            startTime (int, optional)
            endTime (int, optional)

        """
        params = {"symbol": symbol, "interval": interval}
        params.update(kwargs)
        data = self.request("GET", "/api/v1/klines", params)
        return [{
            "openTime": d[0],
            "open": d[1],
            "high": d[2],
            "low": d[3],
            "close": d[4],
            "volume": d[5],
            "closeTime": d[6],
            "quoteVolume": d[7],
            "numTrades": d[8],
        } for d in data]

    def balances(self):
        """Get current balances for all symbols."""
        data = self.signed_request("GET", "/api/v3/account", {'recvWindow': 60000})
        if 'msg' in data:
            raise ValueError("Error from exchange: {}".format(data['msg']))

        return {d["asset"]: {
            "free": d["free"],
            "locked": d["locked"],
        } for d in data.get("balances", [])}

    def cross_free(self):
        """Get current free balances for all symbols in cross margin account"""

        data = self.signed_request("GET", "/sapi/v1/margin/account", {'recvWindow': 60000})
        if 'msg' in data:
            raise ValueError("Error from exchange: {}".format(data['msg']))

        return {d["asset"]: {
            "net": d["free"]
            } for d in data.get("userAssets", [])}

    def margin_balances(self):
        """Get current net balances for all symbols in cross margin account"""

        data = self.signed_request("GET", "/sapi/v1/margin/account", {'recvWindow': 60000})
        if 'msg' in data:
            raise ValueError("Error from exchange: {}".format(data['msg']))

        return {d["asset"]: {
            "net": d["netAsset"]
            } for d in data.get("userAssets", [])}

    def isolated_free(self):
        """Get current free balances for alsymbols in isolated account"""

        data = self.signed_request("GET", "/sapi/v1/margin/isolated/account", {'recvWindow': 60000})
        if 'msg' in data:
            raise ValueError("Error from exchange: {}".format(data['msg']))

        return {d['symbol']: {d['quoteAsset']['asset']: d['quoteAsset']['free'],
                              d['baseAsset']['asset']: d['baseAsset']['free']} for d in
                data.get('assets', {})}

    def isolated_balances(self):
        """Get current net balances for alsymbols in margin account"""

        data = self.signed_request("GET", "/sapi/v1/margin/isolated/account", {'recvWindow': 60000})
        if 'msg' in data:
            raise ValueError("Error from exchange: {}".format(data['msg']))

        return {d['symbol']: {d['quoteAsset']['asset']: d['quoteAsset']['netAsset'],
                              d['baseAsset']['asset']: d['baseAsset']['netAsset']} for d in
                data.get('assets', {})}

    def get_cross_margin_pairs(self):
        """
        Get list of pairs that support cross margin trading
        """
        data = self.signed_request("GET", "/sapi/v1/margin/allPairs", {})
        return [key['base'] + key['quote'] for key in data]

    def get_isolated_margin_pairs(self):
        """
        Get list of pairs that support isolated margin trading
        """
        data = self.signed_request("GET", "/sapi/v1/margin/isolated/allPairs", {})
        return [x['symbol'] for x in data]

    def exchange_info(self):
        """get exchange_info for all sumbols"""
        data = self.request("GET", "/api/v3/exchangeInfo", {})

        return {item['symbol']:item for item in data['symbols']}

    def my_margin_trades(self, symbol, isolated):
        """ Get open margin trades """
        params = {
            "symbol": symbol,
            "isIsolated": isolated,
            }
        data = self.signed_request("GET", "/sapi/v1/margin/myTrades", params)
        return data

    def spot_order(self, symbol, side, quantity, order_type, test=False, **kwargs):
        """Send in a new order.

        Args:
            symbol (str)
            side (str): self.buy or self.sell.
            quantity (float, str or decimal)
            price (float, str or decimal)
            order_type (str, optional): self.limit or self.market.
            newClientOrderId (str, optional): A unique id for the order.
                Automatically generated if not sent.
            stopPrice (float, str or decimal, optional): Used with stop orders.
            icebergQty (float, str or decimal, optional): Used with iceberg orders.

        """
        if order_type == "self.market":
            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": self.format_number(quantity),
            }
        else:
            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": self.format_number(quantity),
            }

        params.update(kwargs)
        path = "/api/v3/order/test" if test else "/api/v3/order"
        data = self.signed_request("POST", path, params)
        return data

    def margin_borrow(self, symbol, quantity, isolated=False, asset=None):
        """
        Borrow funds for margin trade
        """
        params = {
            "asset": asset,
            "amount": self.format_number(quantity),
            "isIsolated": isolated,
            "symbol": symbol,
            }

        path = "/sapi/v1/margin/loan"
        data = self.signed_request("POST", path, params)
        return data

    def margin_repay(self, symbol, quantity, isolated=False, asset=None):
        """
        Repay borrowed margin funds
        """
        params = {
            "symbol": symbol,
            "amount": self.format_number(quantity),
            "isIsolated": isolated,
            "asset": asset,
            }

        path = "/sapi/v1/margin/repay"
        data = self.signed_request("POST", path, params)
        return data

    def get_cross_margin_details(self):
        """
        Get cross margin account details
        """

        path = "/sapi/v1/margin/account"
        data = self.signed_request("GET", path, params={})
        return data

    def get_isolated_margin_details(self, pair=None):
        """
        Get isolated margin account details
        """

        path = "/sapi/v1/margin/isolated/account"
        params = {'symbols':pair} if pair else {}
        data = self.signed_request("GET", path, params=params)

        return data

    def transfer_isolated(self, asset, symbol, direction):
        """"
        Transfer assets between isolated margin and spot accounts
        """
        if direction == "to_isolated":
            trans_from = "SPOT"
            trans_to = "ISOLATED_MARGIN"
            try:
                amount = self.balances()[asset]['free']
            except KeyError:
                print("No such asset")
                return False

        elif direction == "from_isolated":
            trans_from = "ISOLATED_MARGIN"
            trans_to = "SPOT"
            try:
                amount = self.isolated_balances()[symbol][asset]
            except KeyError:
                print("No such symbol or asset {} {}".format(symbol, asset))
                return False
        else:
            print("Invalid direction")
            return False

        params = {
            "asset": asset,
            "symbol": symbol,
            "transFrom": trans_from,
            "transTo": trans_to,
            "amount": amount
        }
        path = "/sapi/v1/margin/isolated/transfer"
        if float(amount) > 0:
            data = self.signed_request("POST", path, params)
            return data
        else:
            return False

    def margin_order(self, symbol, side, quantity, order_type, isolated=False, **kwargs):
        """
        Open a margin trade
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": self.format_number(quantity),
            "isIsolated": isolated,
            }
        params.update(kwargs)
        path = "/sapi/v1/margin/order"
        data = self.signed_request("POST", path, params)
        return data

    def order_status(self, symbol, **kwargs):
        """Check an order's status.

        Args:
            symbol (str)
            orderId (int, optional)
            origClientOrderId (str, optional)
            recvWindow (int, optional)

        """
        params = {"symbol": symbol}
        params.update(kwargs)
        data = self.signed_request("GET", "/api/v3/order", params)
        return data

    def cancel(self, symbol, **kwargs):
        """Cancel an active order.

        Args:
            symbol (str)
            orderId (int, optional)
            origClientOrderId (str, optional)
            newClientOrderId (str, optional): Used to uniquely identify this
                cancel. Automatically generated by default.
            recvWindow (int, optional)

        """
        params = {"symbol": symbol}
        params.update(kwargs)
        data = self.signed_request("DELETE", "/api/v3/order", params)
        return data

    def get_max_borrow(self, asset='USDT', isolated_pair=None):
        """
        Max amount left to borrow in USDT from cross margin account
        """

        if isolated_pair:
            params = {"asset": asset, "isolatedSymbol": isolated_pair}
        else:
            params = {"asset": asset}
        data = self.signed_request("GET", "/sapi/v1/margin/maxBorrowable", params)
        return float(data['amount']) if 'amount' in data else 0

    def get_margin_debt(self):
        """
        Get debts for all cross margin assets
        """
        data = self.signed_request("GET", "/sapi/v1/margin/account", {})
        borrowed = {item['asset']: item['borrowed'] for item in data['userAssets']
                    if item['borrowed'] != '0'}
        return borrowed

    def open_orders(self, symbol, **kwargs):
        """Get all open orders on a symbol.

        Args:
            symbol (str)
            recvWindow (int, optional)

        """
        params = {"symbol": symbol}
        params.update(kwargs)
        data = self.signed_request("GET", "/api/v3/openOrders", params)
        return data

    def all_orders(self, symbol, **kwargs):
        """Get all account orders; active, canceled, or filled.

        If orderId is set, it will get orders >= that orderId. Otherwise most
        recent orders are returned.

        Args:
            symbol (str)
            orderId (int, optional)
            limit (int, optional): Default 500; max 500.
            recvWindow (int, optional)

        """
        params = {"symbol": symbol}
        params.update(kwargs)
        data = self.signed_request("GET", "/api/v3/allOrders", params)
        return data

    def my_trades(self, symbol, **kwargs):
        """Get trades for a specific account and symbol.

        Args:
            symbol (str)
            limit (int, optional): Default 500; max 500.
            fromId (int, optional): TradeId to fetch from. Default gets most recent
                trades.
            recvWindow (int, optional)

        """
        params = {"symbol": symbol, "recvWindow": 60000}
        params.update(kwargs)
        data = self.signed_request("GET", "/api/v3/myTrades", params)
        return data

    @staticmethod
    def retry_session(retries, session=None, backoff_factor=0.3):
        """
        retry requests session
        """
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            method_whitelist=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def request(self, method, path, params=None):
        """
        Make request to API and return result
        """
        session = self.retry_session(retries=5)
        resp = session.request(method, self.endpoint + path, params=params, timeout=60)
        data = resp.json()
        if self.debug:
            print(inspect.stack()[1].function, data)
        else:
            print("Calling binance api path ", path)
        return data

    def signed_request(self, method, path, params):
        """
        Send authenticated request
        """
        if "apiKey" not in self.options or "secret" not in self.options:
            raise ValueError("Api key and secret must be set")

        query = urlencode(sorted(params.items()))
        query += "&timestamp={}".format(int(time.time() * 1000))
        secret = bytes(self.options["secret"].encode("utf-8"))
        signature = hmac.new(secret, query.encode("utf-8"),
                             hashlib.sha256).hexdigest()
        query += "&signature={}".format(signature)

        session = self.retry_session(retries=5)
        resp = session.request(method,
                               self.endpoint + path + "?" + query, timeout=60,
                               headers={"X-MBX-APIKEY": self.options["apiKey"]})
        data = resp.json()
        if self.debug:
            print(inspect.stack()[1].function, data)
        else:
            print("Calling binance api path ", path)
        return data

    @staticmethod
    def format_number(number):
        """
        Format decimal to 8dp if float
        """
        if isinstance(number, float):
            return "{:.8f}".format(number)
        else:
            return str(number)
