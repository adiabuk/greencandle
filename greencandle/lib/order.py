#pylint: disable=no-member,too-many-locals,too-many-lines,broad-except,logging-fstring-interpolation
"""
Buy/Sell orders
"""

from collections import defaultdict
import datetime
import time
import re
from pathlib import Path
from send_nsca3 import send_nsca
from str2bool import str2bool
from greencandle.lib.auth import binance_auth
from greencandle.lib.binance import BinanceException
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.mysql import Mysql
from greencandle.lib.redis_conn import Redis
from greencandle.lib.web import get_drain
from greencandle.lib.binance_accounts import get_binance_spot, base2quote, quote2base, \
        get_binance_isolated, get_binance_cross, get_max_borrow
from greencandle.lib.balance_common import get_base, get_quote, get_step_precision
from greencandle.lib.common import perc_diff, add_perc, sub_perc, AttributeDict, QUOTES
from greencandle.lib.alerts import send_slack_trade, send_slack_message

GET_EXCEPTIONS = exception_catcher((Exception))

class InvalidTradeError(Exception):
    """
    Custom Exception for invalid trade type of trade direction
    """

class Trade():
    """Buy & Sell class"""

    def __init__(self, interval=None, test_data=False, test_trade=False, config=None):
        self.logger = get_logger(__name__)
        self.test_data = test_data
        self.test_trade = test_trade
        self.config = config
        self.prod = str2bool(self.config.main.production)
        self.client = binance_auth()
        self.interval = interval

    @staticmethod
    def is_float(element: any) -> bool:
        """
        check if variable is a float
        return True|False
        """
        # If you expect None to be passed:
        if element is None:
            return False
        try:
            float(element)
            return True
        except ValueError:
            return False

    def is_in_drain(self):
        """
        Check if current scope is in drain given date range, and current time
        Drain time is set in config (drain/drain_range)
        or by the existance of /var/local/drain/{env}_drain file
        """
        currentime = datetime.datetime.now()
        time_str = currentime.strftime('%H:%M')
        raw_range = self.config.main.drain_range.strip()
        start, end = re.findall(r"\d\d:\d\d\s?-\s?\d\d:\d\d", raw_range)[0].split('-')
        time_range = (start.strip(), end.strip())
        drain = str2bool(self.config.main.drain)
        api_drain = get_drain(env=self.config.main.base_env,
                              interval=self.config.main.interval,
                              direction=self.config.main.trade_direction)
        if time_range[1] < time_range[0]:
            return time_str >= time_range[0] or time_str <= time_range[1]
        return (time_range[0] <= time_str <= time_range[1]) if drain else api_drain


    def __send_redis_trade(self, **kwargs):
        """
        Send trade event to redis
        """
        valid_keys = ["pair", "open_time", "current_time", "price", "interval", "event"]
        kwargs = AttributeDict(kwargs)
        for key in valid_keys:
            if key not in valid_keys:
                raise KeyError(f"Missing param {key}")

        self.logger.debug('Strategy - Adding to redis')
        redis = Redis()
        try:
            mepoch = redis.get_intervals(kwargs.pair, kwargs.interval)[-1]
        except IndexError:
            # if unable to get latest time from redis
            mepoch = int(time.time()*1000)

        data = {"event":{"result": kwargs.event,
                         "current_price": format(float(kwargs.price), ".20f"),
                         "date": mepoch,
                        }}

        redis.append_data(kwargs.pair, kwargs.interval, data)
        if kwargs.event == 'CLOSE':
            redis.rm_on_entry(kwargs.pair, 'take_profit_perc')
            redis.rm_on_entry(kwargs.pair, 'stop_loss_perc')
            redis.rm_drawup(kwargs.pair)
            redis.rm_drawdown(kwargs.pair)
        del redis

    def check_pairs(self, items_list):
        """
        Check we can trade which each of given trading pairs
        Return filtered list
        """

        dbase = Mysql(test=self.test_data, interval=self.interval)
        current_trades = dbase.get_trades(direction=self.config.main.trade_direction)
        avail_slots = int(self.config.main.max_trades) - len(current_trades)
        self.logger.info("%s open slots available", avail_slots)
        table = dbase.fetch_sql_data('show tables like "tmp_pairs"', header=False)
        tmp_pairs = dbase.fetch_sql_data('select pair from tmp_pairs', header=False) \
                if table else []
        db_pairs = [x[0] for x in tmp_pairs] if tmp_pairs else {}
        final_list = []
        manual = "any" in self.config.main.name
        good_pairs = str2bool(self.config.main.good_pairs)

        if self.is_in_drain() and not self.test_data:
            msg = "strategy is in drain for pair {str(items_list)}, skipping..."
            self.logger.info(msg)
            send_slack_message("alerts", msg)
            return []

        for item in items_list:

            if not self.test_trade:

                account = 'margin' if 'margin' in self.config.main.trade_type else 'binance'
                totals = self.get_total_amount_to_use(dbase, item[0], account=account)
                if sum(totals.values()) == 0:
                    self.logger.warning("Insufficient funds available for %s %s, skipping...",
                                        self.config.main.trade_direction, item[0])
                    continue

            if (current_trades and [trade for trade in current_trades if item[0] in trade]):
                self.logger.warning("we already have a trade of %s %s, skipping...",
                    self.config.main.trade_direction, item[0])
            elif not manual and (item[0] not in self.config.main.pairs and not self.test_data):
                self.logger.critical("pair %s not in main_pairs, skipping...", item[0])
            elif not manual and good_pairs and db_pairs and (item[0] not in db_pairs
                                                             and not self.test_data):
                self.logger.warning("pair %s not in db_pairs, skipping...", item[0])
                send_slack_message("trades", f"pair {item[0]} not in db_pairs, skipping...")


            elif self.is_float(item[4]) and \
                    ((float(item[4]) > 0 and self.config.main.trade_direction == "short") or \
                    (float(item[4]) < 0 and self.config.main.trade_direction == "long")):
                self.logger.info("wrong trade direction %s", self.config.main.trade_direction)
            elif avail_slots <= 0:
                pairs_str = ', '.join((x[0] for x in items_list))
                self.logger.warning("Too many trades for %s, skipping:%s",
                                    self.config.main.trade_direction, pairs_str)
                msg = f"Too many {self.config.main.trade_direction} trades, skipping {pairs_str}"
                send_slack_message("alerts", msg)
            else:
                final_list.append(item)
                avail_slots -= 1
        if avail_slots >= 1:
            status = 0
        elif avail_slots < 1:
            status = 1
        else:
            status = 3
        try:
            send_nsca(status=status, host_name='jenkins',
                      service_name=f"slots_{self.config.main.name}",
                      text_output=f"Avail Slots:{avail_slots}", remote_host='nagios.amrox.loc')
        except Exception:
            self.logger.warning("Unable to push stats to nagios")
        return final_list

    def open_trade(self, items_list, stop=0):
        """
        Main open trade method
        Will choose between spot/margin and long/short
        """
        items_list = self.check_pairs(items_list)
        if not items_list:
            self.logger.debug("no items to open trade with")
            return False

        if self.config.main.trade_type == "spot":
            if self.config.main.trade_direction == "long":
                result = self.__open_spot_long(items_list)
            else:
                raise InvalidTradeError("Invalid trade direction for spot")

        elif self.config.main.trade_type == "margin":
            if self.config.main.trade_direction == "long":
                result = self.__open_margin_long(items_list, stop)
            elif self.config.main.trade_direction == "short":
                result = self.__open_margin_short(items_list, stop)
            else:
                raise InvalidTradeError("Invalid trade direction")

        else:
            raise InvalidTradeError("Invalid trade type")
        return result

    def close_trade(self, items_list, drawdowns=None, drawups=None):
        """
        Main close trade method
        Will choose between spot/margin and long/short
        """
        additional_trades = []
        if not items_list:
            self.logger.debug("no items to open trade with")
            return False
        if Path(f'/var/local/drain/{self.config.main.base_env}_drain_close').is_file():
            self.logger.info("strategy is in close drain for pair %s, skipping...", items_list)
            return False


        for item in items_list:

            # Number of trades within scope
            dbase = Mysql(test=self.test_data, interval=self.interval)
            count = dbase.fetch_sql_data(f"select count(*) from trades where close_price "
                                         f"is NULL and pair like '%{item[0]}' and "
                                         f"name='{self.config.main.name}' "
                                         f"and direction='{self.config.main.trade_direction}'",
                                         header=False)[0][0]

            while count -1 > 0:
                additional_trades.append(item)
                count -= 1

        items_list += additional_trades

        if self.config.main.trade_type == "spot":
            if self.config.main.trade_direction == "long":
                result = self.__close_spot_long(items_list, drawdowns=drawdowns, drawups=drawups)
            else:
                raise InvalidTradeError("Invalid trade direction for spot")

        elif self.config.main.trade_type == "margin":
            if self.config.main.trade_direction == "long":
                result = self.__close_margin_long(items_list, drawdowns=drawdowns, drawups=drawups)
            elif self.config.main.trade_direction == "short":
                result = self.__close_margin_short(items_list, drawdowns=drawdowns, drawups=drawups)
            else:
                raise InvalidTradeError("Invalid trade direction")

        else:
            raise InvalidTradeError("Invalid trade type")

        return result

    def get_borrowed(self, pair, symbol):
        """
        get amount borrowed from exchange for both cross and isolated modes
        for a particular pair/direction
        """

        if not str2bool(self.config.main.isolated):
            # if we are attempting a cross trade
            details = self.client.get_cross_margin_details()
            for item in details['userAssets']:
                borrowed = float(item['borrowed'])
                asset = item['asset']
                if asset == symbol:
                    return borrowed if borrowed else 0

        elif str2bool(self.config.main.isolated):
            # if we are attempting an isolated trade
            details = self.client.get_isolated_margin_details(pair)
            if details['assets'][0]['quoteAsset']['asset'] == symbol:
                return float(details['assets'][0]['quoteAsset']['borrowed'])
            if details['assets'][0]['baseAsset']['asset'] == symbol:
                return float(details['assets'][0]['baseAsset']['borrowed'])
        return 0

    def get_avail_asset(self, symbol):
        """
        Get amount of available asset in wallet
        Will check if we are isolated/cross environment
        """
        if str2bool(self.config.main.isolated):
            bals = get_binance_isolated()['isolated']
        else:
            bals = get_binance_cross()['margin']
        try:
            return float(bals[symbol]['gross_count'])
        except KeyError:
            return 0

    def get_balance_to_use(self, dbase, account=None, pair=None, total_max=0):
        """
        Choose between spot/cross/isolated/test balances
        Retrive dict and return appropriate value
        Only return 99% of the value
        Returns: float in base if short, or quote if long
        """
        symbol = get_quote(pair) if self.config.main.trade_direction == 'long' else get_base(pair)
        test_balances = self.get_test_balance(dbase, account=account)[account]
        final = 0
        if self.test_data or self.test_trade:
            if self.config.main.trade_direction == 'short' and symbol not in test_balances:
                usd = test_balances['USDT']['count']
                final = quote2base(usd, symbol +'USDT')
            else:
                final = test_balances[symbol]['count']

        elif account == 'binance':
            try:
                final = float(get_binance_spot()[account][symbol]['count'])
            except KeyError:
                pass

        elif account == 'margin' and str2bool(self.config.main.isolated):
            try:
                final = float(self.client.isolated_free()[pair][symbol])
            except KeyError:
                pass

        elif account == 'margin' and not str2bool(self.config.main.isolated):
            try:
                final = float(self.client.cross_free()[symbol]['net'])
            except KeyError:
                pass

        # Use 99% of amount determined by divisor
        return_symbol = sub_perc(1, final / float(self.config.main.divisor)) if final else 0
        return_usd = return_symbol if 'USD' in symbol else base2quote(return_symbol, symbol+'USDT')

        # Don't use up all remaining balance for long trades
        # or when a large balance for given symbol is available
        if total_max and return_symbol and 'USD' in symbol:
            return_symbol = min(total_max, return_symbol)
            return_usd = min(total_max, return_usd)
        elif total_max and return_symbol and 'USD' not in symbol:
            return_symbol = min(quote2base(total_max, symbol+'USDT'), return_symbol)
            return_usd = base2quote(return_symbol, symbol+'USDT')

        return_dict = {"symbol": return_symbol,
                       "symbol_name": symbol,
                       "usd": return_usd}
        return return_dict

    def get_amount_to_borrow(self, pair, dbase):
        """
        Get amount to borrow based on pair, and trade direction
        divide by divisor and return in the symbol we need to borrow
        Only return 99% of the value
        Returns: float in base if short, or quote if long
        """
        return_dict = {}
        orig_base = get_base(pair)
        orig_quote = get_quote(pair)
        borrow_drain = Path('/var/local/drain/borrow_drain').is_file()

        if borrow_drain:
            return_dict['usd'] = 0
            return_dict['symbol'] = 0
            self.logger.info("Will skip borrow for pair %s due to borrow drain", pair)
            return return_dict

        # get current borrowed
        mode = "isolated" if str2bool(self.config.main.isolated) else "cross"
        rows = dbase.get_current_borrowed(pair if mode == 'isolated' else '', mode)
        borrowed_usd = 0
        # go through open trades
        for (current_pair, amt, direction) in list(rows):
            base = get_base(current_pair)
            quote = get_quote(current_pair)
            if direction == "long":
                borrowed_usd += float(amt) if 'USD' in quote else base2quote(amt, quote+"USDT")
            elif direction == "short":
                borrowed_usd += float(amt) if 'USD' in base else base2quote(amt, base+"USDT")
            # get aggregated total borrowed in USD

        # get (addiontal) amount we can borrow
        try:
            _, max_borrow_usd = get_max_borrow(pair)
        except BinanceException as binex:
            self.logger.error(f"TRADE: borrow error-open "
                              f"{self.config.main.trade_direction} {pair} while "
                              f"trying to fetch borrow amount: {str(binex)}")
            max_borrow_usd = 0

        # sum of total borrowed and total borrowable
        total = (float(borrowed_usd) + float(max_borrow_usd))

        # divide total by divisor
        # convert to quote asset if not USDT

        # long
        if self.config.main.trade_direction == "long":
            if "USD" in orig_quote:
                value = sub_perc(1, total / float(self.config.main.divisor))
                return_dict['usd'] = value
                return_dict['symbol'] = value
            else:
                final_symbol = sub_perc(1, quote2base(total, orig_quote+"USDT") /
                                        float(self.config.main.divisor))
                final_usd = sub_perc(1, total / float(self.config.main.divisor))

                usd_value = sub_perc(1, total / float(self.config.main.divisor))
                value = quote2base(usd_value, orig_quote+'USDT')
                return_dict['usd'] = final_usd
                return_dict['symbol'] = final_symbol

        # convert to base asset if we are short
        # short
        else:  # amt in base
            usd_value = sub_perc(1, total/float(self.config.main.divisor))
            value = quote2base(usd_value, orig_base+'USDT')
            final_symbol = sub_perc(1, quote2base(total, orig_base+'USDT') /
                                    float(self.config.main.divisor))
            final_usd = sub_perc(1, total / float(self.config.main.divisor))
            return_dict['usd'] = final_usd
            return_dict['symbol'] = final_symbol
            return return_dict


        # Use 99% of amount determined by divisor
        # and check if we have exceeded max_borrable amount
        if (orig_quote == 'USDT' and return_dict['usd'] > max_borrow_usd and
                self.config.main.trade_direction == "long"):
            value = sub_perc(10, max_borrow_usd)
            return_dict['usd'] = value
            return_dict['symbol'] = value
            return return_dict

        if (orig_quote != 'USDT' and
                base2quote(return_dict['symbol'], orig_quote+'USDT') > max_borrow_usd and
                self.config.main.trade_direction == "long"):
            usd_value = sub_perc(10, max_borrow_usd)
            base_value = quote2base(usd_value, orig_quote+'USDT')
            return_dict['usd'] = usd_value
            return_dict['symbol'] = base_value
            return return_dict

        return return_dict

    def get_total_amount_to_use(self, dbase, pair=None, account=None, max_usd=None):
        """ Get total amount to use as sum of balance_to_use and loan_to_use """

        max_from_db = max_usd if max_usd else dbase.get_var_value('max_trade_usd')
        total_max = int(max_from_db) if max_from_db else int(self.config.main.max_trade_usd)
        balance_to_use = self.get_balance_to_use(dbase, account, pair, total_max)
        # set default loan to use as 0, may be overwritten if non-spot and not enough balance to
        # cover max, where loan is available
        loan_to_use = {'symbol': 0, 'usd': 0, 'symbol_name': balance_to_use['symbol_name']}
        prev_loan = dbase.get_extra_loan_amt(balance_to_use['symbol_name'])

        # use balance only
        if self.test_trade or balance_to_use['usd'] > (total_max *5) or \
                (str2bool(self.config.main.balance_only) and balance_to_use['usd'] > total_max):

            balance_to_use['usd'] = total_max


            if balance_to_use['symbol_name'] == 'USDT':
                balance_to_use['symbol'] = balance_to_use['usd']
            else:
                balance_to_use['symbol'] = quote2base(balance_to_use['usd'],
                                                      balance_to_use['symbol_name']+'USDT')
                loan_to_use = {'symbol': 0, 'usd': 0, 'symbol_name': balance_to_use['symbol_name']}

        else: # use loan
            loan_to_use = self.get_amount_to_borrow(pair, dbase) if \
                    self.config.main.trade_type != 'spot' else {'usd': 0,
                                                                'symbol': 0,
                                                                'symbol_name':
                                                                balance_to_use['symbol_name']}
            total_remaining = max(total_max - balance_to_use['usd'], 0)
            if loan_to_use['usd'] > total_remaining:
                loan_to_use['usd'] = total_remaining
                loan_to_use['symbol'] = total_remaining if 'USD' in \
                        balance_to_use['symbol_name'] else \
                        quote2base(total_remaining, balance_to_use['symbol_name']+'USDT')

        return_dict = {"balance_amt": balance_to_use['symbol'],
                       "loan_amt": loan_to_use['symbol'],
                       "preloan_amt": prev_loan
                       }

        self.logger.info("TRADE: balance/loan ratio for %s %s - %s", pair,
                         self.config.main.trade_direction, return_dict)
        return return_dict

    def __open_margin_long(self, long_list, stop=0):
        """
        Get item details and attempt to trade according to config
        Returns True|False
        """
        self.logger.info("We need to open margin long %s", long_list)

        dbase = Mysql(test=self.test_data, interval=self.interval)

        for pair, current_time, current_price, event, _, max_usd in long_list:
            if stop > 50:
                self.logger.error(f"stop loss to high to reserve funds, passing margin "
                                  f"{pair}/long")
                continue
            pair = pair.strip()
            total_amt_to_use = self.get_total_amount_to_use(dbase, account='margin', pair=pair,
                                                            max_usd=max_usd)
            amount_to_borrow = total_amt_to_use['loan_amt']
            current_quote_bal = total_amt_to_use['balance_amt']
            preloan_amt= total_amt_to_use['preloan_amt']

            quote = get_quote(pair)

            # amt in base
            quote_to_use = current_quote_bal + amount_to_borrow

            reserve = 1 + float(stop) if float(stop) > 0 else 2
            # allow 1% + stoploss incase trade goes in wrong direction
            base_to_use = get_step_precision(pair, sub_perc(reserve,
                                                            quote2base(quote_to_use, pair)))

            base_not_to_use = (quote2base(quote_to_use, pair)/100)*reserve
            self.logger.info('leaving %s perc of base margin aside (%s %s)',
                             reserve, base_not_to_use, get_base(pair))
            self.logger.info("TRADE: opening margin long %s base of %s with %s quote at %s price",
                             base_to_use, pair, current_quote_bal+amount_to_borrow, current_price)

            tot_borrowed = preloan_amt + amount_to_borrow
            tot_borrowed_usd = tot_borrowed if quote == 'USDT' else \
                    base2quote(tot_borrowed, quote+'USDT')
            dbase.update_extra_loan(quote)

            if self.prod:

                if float(amount_to_borrow) <= 0:
                    self.logger.info("Borrow amount is zero for pair %s open long. Continuing",
                                     pair)
                    amt_str = get_step_precision(pair, quote2base(current_quote_bal, pair))
                else:  # amount to borrow

                    amt_str = base_to_use
                    try:
                        borrow_res = self.client.margin_borrow(
                            symbol=pair, quantity=amount_to_borrow,
                            isolated=str2bool(self.config.main.isolated),
                            asset=quote)
                    except BinanceException as binex:
                        self.logger.error(f"TRADE: borrow error-open long {pair} while "
                                          f"trying to borrow {amount_to_borrow} {quote}: "
                                          f"{str(binex)}")
                        return False

                    self.logger.info("TRADE: borrowed %s of %s for long pair %s Balance: %s "
                                     "borrow_res: %s",
                                     amount_to_borrow, quote, pair, current_quote_bal, borrow_res)
                try:
                    trade_result = self.client.margin_order(symbol=pair, side=self.client.buy,
                                                            quantity=amt_str,
                                                            order_type=self.client.market,
                                                            isolated=str2bool(
                                                                self.config.main.isolated))

                except BinanceException as binex:
                    self.logger.error(f"TRADE: error-open {self.config.main.trade_direction} "
                                      f"{pair}: {str(binex)}")

                    self.logger.critical("%s/long Vars: base quantity:%s, quote_quantity: %s "
                                         "quote  bal:%s, quote_borrowed: %s", pair, amt_str,
                                         quote_to_use, current_quote_bal, amount_to_borrow)
                    return False
                self.logger.info("TRADE: %s open margin long result: %s", pair, trade_result)

                # override values from exchange if in prod
                fill_price, amt_str, quote_to_use, order_id = \
                        self.__get_result_details(current_price, trade_result)

            else: # not prod
                amt_str = base_to_use
                order_id = 0
                fill_price = current_price
                trade_result = {}

            commission_usd = self.__get_commission(trade_result)

            if self.test_data or self.test_trade or \
                    (not self.test_trade and 'transactTime' in trade_result):

                try:
                    amt_str = sub_perc(dbase.get_complete_commission()/2, amt_str)
                except (KeyError, TypeError):  # Empty dict, or no commission for base
                    pass


                dbase.insert_trade(pair=pair, price=fill_price, date=current_time,
                                   quote_amount=quote_to_use, base_amount=amt_str,
                                   borrowed=tot_borrowed, borrowed_usd=tot_borrowed_usd,
                                   divisor=self.config.main.divisor,
                                   direction=self.config.main.trade_direction,
                                   symbol_name=quote, commission=str(commission_usd),
                                   order_id=order_id, comment=event)

                self.__send_notifications(pair=pair, open_time=current_time,
                                          fill_price=fill_price, interval=self.interval,
                                          event=event, action='OPEN', usd_profit='N/A',
                                          quote=quote_to_use, close_time='N/A')

        del dbase
        return "opened"

    @staticmethod
    @GET_EXCEPTIONS
    def get_test_balance(dbase, account=None):
        """
        Get and return test balance dict in the same format as binance
        """
        balance = defaultdict(lambda: defaultdict(defaultdict))

        balance[account]['BTC']['count'] = 0.47
        balance[account]['ETH']['count'] = 8.92
        balance[account]['USDT']['count'] = 10000
        balance[account]['USDC']['count'] = 10000
        balance[account]['GBP']['count'] = 10000
        balance[account]['BNB']['count'] = 46.06
        for quote in QUOTES:
            last_value = dbase.fetch_sql_data(f"select quote_in from trades "
                                              f"where pair like '%{quote}' "
                                              f"order by open_time desc limit 1",
                                              header=False)
            last_value = float(last_value[0][0]) if last_value else 0
            balance[account][quote]['count'] = max(last_value, balance[account][quote]['count'])
        return balance

    def __open_spot_long(self, buy_list):
        """
        Get item details and attempt to trade according to config
        Returns True|False
        """
        self.logger.info("We need to open spot long %s", buy_list)

        dbase = Mysql(test=self.test_data, interval=self.interval)

        for pair, current_time, current_price, event, _, max_usd in buy_list:
            quote_amount = self.get_total_amount_to_use(dbase, account='binance',
                                                        pair=pair, max_usd=max_usd
                                                        )['balance_amt']

            quote = get_quote(pair)

            if quote_amount <= 0:
                self.logger.critical("Unable to get balance %s for quote %s while trading %s "
                                     "spot long", quote_amount, quote, pair)
                return False

            amount = quote2base(quote_amount, pair)

            self.logger.info("TRADE: opening spot long %s base of %s with %s quote at %s price",
                             amount, pair, quote_amount, quote)
            self.logger.debug("amount to buy: %s, current_price: %s, amount:%s",
                              quote_amount, current_price, amount)
            if self.prod and not self.test_data:
                amt_str = get_step_precision(pair, amount)
                try:
                    trade_result = self.client.spot_order(symbol=pair, side=self.client.buy,
                                                          quantity=amt_str,
                                                          order_type=self.client.market,
                                                          test=self.test_trade)

                except BinanceException as binex:
                    self.logger.error(f"Trade error-open {pair}: {str(binex)}")
                    self.logger.critical("Vars: quantity:%s, bal:%s", amt_str, quote_amount)
                    return False

                # override values from exchange if in prod
                self.logger.info("%s open spot long result: %s", pair, trade_result)
                fill_price, amount, quote_amount, order_id = \
                        self.__get_result_details(current_price, trade_result)

            else:
                trade_result = True
                order_id = 0
                fill_price = current_price
                trade_result = {}

            commission_usd = self.__get_commission(trade_result)

            if self.test_data or self.test_trade or \
                    (not self.test_trade and 'transactTime' in trade_result):
                # only insert into db, if:
                # 1. we are using test_data
                # 2. we performed a test trade which was successful - (empty dict)
                # 3. we proformed a real trade which was successful - (transactTime in dict)
                amt_str = amount

                try:
                    amt_str = sub_perc(dbase.get_complete_commission()/2, amt_str)
                except (KeyError, TypeError):  # Empty dict, or no commission for base
                    pass

                db_result = dbase.insert_trade(pair=pair, price=fill_price, date=current_time,
                                               quote_amount=quote_amount, base_amount=amount,
                                               direction=self.config.main.trade_direction,
                                               symbol_name=quote, commission=str(commission_usd),
                                               order_id=order_id, comment=event)
                if db_result:
                    self.__send_notifications(pair=pair, open_time=current_time,
                                              fill_price=fill_price, interval=self.interval,
                                              event=event, action='OPEN', usd_profit='N/A',
                                              quote=quote_amount, close_time='N/A')

        del dbase
        return "opened"

    def __send_notifications(self, perc=None, **kwargs):
        """
        Pass given data to trade notification functions
        """
        valid_keys = ["pair", "fill_price", "event", "action", "usd_profit",
                      "quote", "open_time", "close_time"]

        kwargs = AttributeDict(kwargs)
        for key in valid_keys:
            if key not in valid_keys:
                raise KeyError(f"Missing param {key}")

        current_time = kwargs.close_time if kwargs.action == 'CLOSE' else kwargs.open_time
        self.__send_redis_trade(pair=kwargs.pair, current_time=current_time,
                                price=kwargs.fill_price, interval=self.interval,
                                event=kwargs.action, usd_profit=kwargs.usd_profit)

        usd_quote = kwargs.quote if 'USD' in kwargs.pair else \
                base2quote(kwargs.quote, get_quote(kwargs.pair)+'USDT')

        if 'id' in kwargs:
            dbase = Mysql()
            perc, net_perc, usd_net_profit, drawup, drawdown = \
                    dbase.fetch_sql_data(f"select perc, net_perc, usd_net_profit, drawup_perc, "
                                         f"drawdown_perc from profit where id={kwargs.id}",
                                                            header=False)[0]
        else:
            net_perc = None
            usd_net_profit = None
            drawup = None
            drawdown = None

        send_slack_trade(channel='trades', event=kwargs.event, perc=perc,
                         pair=kwargs.pair, action=kwargs.action, price=kwargs.fill_price,
                         usd_profit=kwargs.usd_profit, quote=kwargs.quote, usd_quote=usd_quote,
                         open_time=kwargs.open_time, close_time=kwargs.close_time,
                         net_perc=net_perc, usd_net_profit=usd_net_profit,
                         drawup=drawup, drawdown=drawdown)

    def __get_result_details(self, current_price, trade_result):
        """
        Extract price, base/quote amt and order id from exchange transaction dict
        Returns:
        Tupple: price, base_amt, quote_amt, order_id
        """
        prices = []
        if 'transactTime' in trade_result:
            # Get price from exchange
            for fill in trade_result['fills']:
                prices.append(float(fill['price']))
            fill_price = sum(prices) / len(prices)
            self.logger.info("%s Current price %s, Fill price: %s",
                             self.config.main.trade_direction, current_price, fill_price)

            return (fill_price,
                    trade_result['executedQty'],
                    trade_result['cummulativeQuoteQty'],
                    trade_result['orderId'])

        return [None] * 4

    def __get_commission(self, trade_result):
        """
        Extract and collate commission from trade result dict

        """
        usd_total = 0
        if self.prod and 'fills' in trade_result and not(self.test_trade or self.test_data):
            for fill in trade_result['fills']:
                if 'USD' in fill['commissionAsset']:
                    usd_total += float(fill['commission'])
                else:
                    # convert to usd
                    usd_total += base2quote(float(fill['commission']),
                                            fill['commissionAsset']+'USDT')
        return usd_total

    def __close_margin_short(self, short_list, drawdowns=None, drawups=None):
        """
        Get item details and attempt to close margin short trade according to config
        Returns True|False
        """

        self.logger.info("we need to close margin short %s", short_list)
        dbase = Mysql(test=self.test_data, interval=self.interval)
        name = self.config.main.name
        for pair, current_time, current_price, event, _, _ in short_list:
            base = get_base(pair)
            quote = get_quote(pair)

            open_price, quote_in, _, base_in, borrowed, _ = dbase.get_trade_value(pair)[0]
            if not open_price:
                self.logger.info("No open trades found for short %s", pair)
                return True
            # Quantity of base_asset we can buy back based on current price
            quantity = base_in

            if not quantity:
                self.logger.info("close_margin_short: unable to get quantity for %s", pair)
                return True

            perc_inc = - (perc_diff(open_price, current_price))
            quote_out = sub_perc(perc_inc, quote_in)

            self.logger.info("TRADE: Closing margin short %s base of %s with %s quote "
                             "for %.15f price",
                             quantity, pair, quote_out, float(current_price))
            if self.prod and not self.test_data:
                amt_str = get_step_precision(pair, quantity)
                try:
                    trade_result = self.client.margin_order(symbol=pair,
                                                            side=self.client.buy,
                                                            quantity=amt_str,
                                                            order_type=self.client.market,
                                                            isolated=str2bool(
                                                                self.config.main.isolated))

                except BinanceException as binex:
                    self.logger.error(f"Trade error-close {pair}: {str(binex)}")
                    return False
                self.logger.info("TRADE: %s close margin short result: %s", pair, trade_result)

                actual_borrowed = self.get_borrowed(pair=pair, symbol=base)
                borrowed = float(actual_borrowed) if float(borrowed) > float(actual_borrowed) else \
                    float(borrowed)
                time.sleep(5) # wait a while before re-fetching balance
                avail = self.get_avail_asset(base)
                repay = borrowed if avail > borrowed else avail
                repay_drain = Path('/var/local/drain/repay_drain').is_file()
                if repay_drain:
                    self.logger.info("Will skip repaying for pair %s due to repay drain",
                                     pair)
                    repay = 0

                if float(repay) > 0:
                    try:
                        repay_result = self.client.margin_repay(
                            symbol=pair, quantity=repay,
                            isolated=str2bool(self.config.main.isolated),
                            asset=base)
                    except BinanceException as binex:
                        self.logger.error(f"TRADE: repay error-close {pair}: {str(binex)}")
                        self.logger.critical("Params: %s, %s, %s %s", pair, borrowed,
                                          self.config.main.isolated, base)

                    self.logger.info("TRADE: repaid: %s %s for pair short %s result: %s",
                                     repay, base, pair, repay_result)
                else:
                    self.logger.info("No borrowed funds to repay for short %s", pair)

                # override values from exchange if in prod
                fill_price, quantity, quote_out, order_id = \
                        self.__get_result_details(current_price, trade_result)
            else:
                order_id = 0
                fill_price = current_price
                trade_result = {}

            commission_usd = self.__get_commission(trade_result)

            if name == "api":
                name = "%"
            drawdown = 0 if not drawdowns else drawdowns[pair]
            drawup = 0 if not drawdowns else drawups[pair]
            result = dbase.update_trades(pair=pair, close_time=current_time,
                                         close_price=fill_price,
                                         quote=quote_out, base_out=quantity, name=name,
                                         drawdown=drawdown, drawup=drawup,
                                         symbol_name=quote, commission=commission_usd,
                                         order_id=order_id, comment=event)
            if result:
                query = (f"select p.open_time, p.usd_profit from trades t, profit p where "
                         f"p.id=t.id and t.pair='{pair}' and t.closed_by='{name}' order "
                         f"by t.id desc limit 1")
                try:
                    open_time, profit = dbase.fetch_sql_data(query, header=False)[0]
                except IndexError:
                    self.logger.error(f"Unable to fetch opentime/profit: {query}")
                    return False

                self.__send_notifications(pair=pair, close_time=current_time,
                                          fill_price=current_price, interval=self.interval,
                                          event=event, action='CLOSE', usd_profit=profit,
                                          quote=quote_out, open_time=open_time, id=result)
            else:
                self.logger.error(f"TRADE: close short Failed {name}:{pair}")

        del dbase
        return "closed"

    def __open_margin_short(self, short_list, stop):
        """
        Get item details and attempt to open margin short trade according to config
        Returns True|False
        """
        self.logger.info("We need to open margin short %s", short_list)
        dbase = Mysql(test=self.test_data, interval=self.interval)

        for pair, current_time, current_price, event, _, max_usd in short_list:
            base = get_base(pair)

            if stop > 50:
                self.logger.error(f"stop loss to high to reserve funds, passing margin "
                                  f"{pair}/short")
                continue
            total_amount_to_use = self.get_total_amount_to_use(dbase, account='margin', pair=pair,
                                                               max_usd=max_usd)
            current_base_bal = total_amount_to_use['balance_amt']
            amount_to_borrow = total_amount_to_use['loan_amt']
            preloan_amt = total_amount_to_use['preloan_amt']


            reserve = 1 + float(stop) if float(stop) > 0 else 2
            # allow 1% + stoploss incase trade goes in wrong direction
            total_base_amount = get_step_precision(pair, sub_perc(reserve, amount_to_borrow +
                                                                  current_base_bal))

            total_quote_amount = base2quote(total_base_amount, pair)

            base_not_to_use = (quote2base(total_quote_amount, pair)/100)*reserve
            self.logger.info('Leaving %s perc of base margin aside (%s %s) for pair %s',
                             reserve, base_not_to_use, get_base(pair), pair)
            self.logger.info("TRADE: opening margin short %s base of %s with %s quote at %s price",
                             total_base_amount, pair, total_quote_amount, current_price)

            tot_borrowed = preloan_amt + amount_to_borrow
            tot_borrowed_usd = tot_borrowed if base == 'USDT' else \
                    base2quote(tot_borrowed, base+'USDT')
            dbase.update_extra_loan(base)


            if self.prod:
                if float(amount_to_borrow) <= 0:
                    self.logger.info("Borrow amount is zero for short pair %s.  Continuing", pair)
                    amt_str = total_base_amount

                else:  # amount to borrow
                    amt_str = total_base_amount
                    try:
                        borrow_res = self.client.margin_borrow(
                            symbol=pair, quantity=amount_to_borrow,
                            isolated=str2bool(self.config.main.isolated),
                            asset=base)
                    except BinanceException as binex:
                        self.logger.error(f"TRADE: borrow error-open short {pair} "
                                          f"while trying to borrow {amount_to_borrow} {base}: "
                                          f"{str(binex)}")
                        return False

                    self.logger.info("TRADE: borrowed %s of %s for short pair %s "
                                     "Balance: %s, borrow_res:%s",
                                     amount_to_borrow, base, pair, total_base_amount,
                                     borrow_res)
                try:
                    trade_result = self.client.margin_order(symbol=pair, side=self.client.sell,
                                                            quantity=amt_str,
                                                            order_type=self.client.market,
                                                            isolated=str2bool(
                                                                self.config.main.isolated))
                except BinanceException as binex:
                    self.logger.error("TRADE: short trade error-open %s: %s", pair, str(binex))
                    self.logger.critical("%s/short Vars: quantity:%s, bal:%s, borrowed: %s",
                                      pair, amt_str, current_base_bal, amount_to_borrow)
                    return False

                self.logger.info("%s open margin short result: %s", pair, trade_result)

                # override values from exchange if in prod
                fill_price, amt_str, total_quote_amount, order_id = \
                        self.__get_result_details(current_price, trade_result)

            else:  # not prod
                amt_str = total_base_amount
                order_id = 0
                fill_price = current_price
                trade_result = {}

            commission_usd = self.__get_commission(trade_result)

            if self.test_data or self.test_trade or \
                    (not self.test_trade and 'transactTime' in trade_result):

                try:
                    amt_str = sub_perc(dbase.get_complete_commission()/2, amt_str)
                except (KeyError, TypeError):  # Empty dict, or no commission for base
                    pass

                dbase.insert_trade(pair=pair, price=fill_price, date=current_time,
                                   quote_amount=total_quote_amount,
                                   base_amount=amt_str, borrowed=tot_borrowed,
                                   borrowed_usd=tot_borrowed_usd,
                                   divisor=self.config.main.divisor,
                                   direction=self.config.main.trade_direction,
                                   symbol_name=get_quote(pair), commission=str(commission_usd),
                                   order_id=order_id, comment=event)

                self.__send_notifications(pair=pair, open_time=current_time,
                                          fill_price=current_price, interval=self.interval,
                                          event=event, action='OPEN', usd_profit='N/A',
                                          quote=total_quote_amount, close_time='N/A')
        del dbase
        return "opened"

    def __close_spot_long(self, sell_list, drawdowns=None, drawups=None):
        """
        Get item details and attempt to close spot trade according to config
        Returns True|False
        """

        self.logger.info("we need to close spot long %s", sell_list)
        dbase = Mysql(test=self.test_data, interval=self.interval)
        name = self.config.main.name
        for pair, current_time, current_price, event, _, _ in sell_list:
            quantity = dbase.get_quantity(pair)

            if not quantity:
                self.logger.info("close_spot_long: unable to find quantity for %s", pair)
                return True

            open_price, quote_in, _, _, _, _ = dbase.get_trade_value(pair)[0]
            if not open_price:
                self.logger.info("No open trades found for spot %s", pair)
                return True

            perc_inc = perc_diff(open_price, current_price)
            quote_out = add_perc(perc_inc, quote_in)

            self.logger.info("TRADE: closing spot long %s of %s with %s quote for %.15f price",
                             quantity, pair, quote_out, float(current_price))
            if self.prod and not self.test_data:

                amt_str = get_step_precision(pair, quantity)
                try:
                    trade_result = self.client.spot_order(
                        symbol=pair, side=self.client.sell, quantity=amt_str,
                        order_type=self.client.market, test=self.test_trade)

                except BinanceException as binex:
                    self.logger.error(f"TRADE: Long Trade error-close {pair}: {str(binex)}")
                    return False

                self.logger.info("%s close spot long result: %s", pair, trade_result)
                # override values from exchange if in prod
                fill_price, quantity, quote_out, order_id = \
                        self.__get_result_details(current_price, trade_result)

            else:  # not prod
                order_id = 0
                fill_price = current_price
                trade_result = {}

            commission_usd = self.__get_commission(trade_result)

            if self.test_data or self.test_trade or \
                    (not self.test_trade and 'transactTime' in trade_result):
                if name == "api":
                    name = "%"

                drawdown = 0 if not drawdowns else drawdowns[pair]
                drawup = 0 if not drawdowns else drawups[pair]
                result = dbase.update_trades(pair=pair, close_time=current_time,
                                             close_price=fill_price, quote=quote_out,
                                             base_out=quantity, name=name,
                                             drawdown=drawdown, drawup=drawup,
                                             symbol_name=get_quote(pair), commission=commission_usd,
                                             order_id=order_id, comment=event)
                if result:
                    open_time, profit = dbase.fetch_sql_data(f"select p.open_time, p.usd_profit "
                                                             f"from trades t, profit p where "
                                                             f"p.id=t.id and t.pair='{pair}' and "
                                                             f"t.closed_by='{name}' order by "
                                                             f"t.id desc limit 1", header=False)[0]

                    self.__send_notifications(pair=pair, close_time=current_time,
                                              fill_price=fill_price, interval=self.interval,
                                              event=event, action='CLOSE', usd_profit=profit,
                                              quote=quote_out, open_time=open_time, id=result)
                else:
                    self.logger.error(f"TRADE: Close spot long Failed {name}:{pair}")
                    return False
        del dbase
        return "closed"

    def __close_margin_long(self, sell_list, drawdowns=None, drawups=None):
        """
        Get item details and attempt to close margin long trade according to config
        Returns True|False
        """

        self.logger.info("we need to close margin long %s", sell_list)
        dbase = Mysql(test=self.test_data, interval=self.interval)
        name = self.config.main.name
        for pair, current_time, current_price, event, _, _ in sell_list:
            quantity = dbase.get_quantity(pair)
            if not quantity:
                self.logger.info("close_margin_long: unable to find quantity for %s", pair)
                return True

            open_price, quote_in, _, _, borrowed, _, = dbase.get_trade_value(pair)[0]
            if not open_price:
                self.logger.info("No open trades found for long %s", pair)
                return True

            perc_inc = perc_diff(open_price, current_price)
            quote_out = add_perc(perc_inc, quote_in)

            self.logger.info("TRADE: closing margin long %s base of %s with %s quote "
                             "for %.15f price",
                             quantity, pair, quote_out, float(current_price))
            quote = get_quote(pair)

            if self.prod:
                amt_str = get_step_precision(pair, quantity)
                try:
                    trade_result = self.client.margin_order(symbol=pair, side=self.client.sell,
                                                            quantity=amt_str,
                                                            order_type=self.client.market,
                                                            isolated=str2bool(
                                                                self.config.main.isolated))
                except BinanceException as binex:
                    self.logger.error(f"TRADE: margin long Trade error-close pair: {str(binex)}")
                    return False

                self.logger.info("%s close margin long result: %s", pair, trade_result)
                actual_borrowed = self.get_borrowed(pair=pair, symbol=quote)
                borrowed = float(actual_borrowed) if float(borrowed) > float(actual_borrowed) else \
                        float(borrowed)

                time.sleep(5) # wait a while before re-fetching balance
                avail = self.get_avail_asset(quote)
                repay = borrowed if avail > borrowed else avail
                repay_drain = Path('/var/local/drain/repay_drain').is_file()
                if repay_drain:
                    self.logger.info("Will skip repaying for pair %s due to repay drain",
                                     pair)
                    repay = 0

                if float(repay) > 0:
                    try:
                        repay_result = self.client.margin_repay(
                            symbol=pair, quantity=repay,
                            isolated=str2bool(self.config.main.isolated),
                            asset=quote)
                    except BinanceException as binex:
                        self.logger.error(f"TRADE: repay error-close {pair}: {str(binex)}")
                        self.logger.critical("Params: %s, %s, %s %s", pair, borrowed,
                                          self.config.main.isolated, quote)

                    self.logger.info("TRADE: repaid: %s %s for pair %s result: %s",
                                     repay, quote, pair, repay_result)
                else:
                    self.logger.info("No borrowed funds to repay for %s", pair)

                # override values from exchange if in prod
                fill_price, quantity, quote_out, order_id = \
                        self.__get_result_details(current_price, trade_result)
            else:
                order_id = 0
                fill_price = current_price
                trade_result = {}

            commission_usd = self.__get_commission(trade_result)

            if name == "api":
                name = "%"
            drawdown = 0 if not drawdowns else drawdowns[pair]
            drawup = 0 if not drawdowns else drawups[pair]
            result = dbase.update_trades(pair=pair, close_time=current_time,
                                         close_price=fill_price, quote=quote_out,
                                         base_out=quantity, name=name,
                                         drawdown=drawdown,
                                         drawup=drawup, symbol_name=quote,
                                         commission=commission_usd, order_id=order_id,
                                         comment=event)
            if result:
                open_time, profit = dbase.fetch_sql_data(f"select p.open_time, p.usd_profit "
                                                         f"from trades t, profit p where "
                                                         f"p.id=t.id and t.pair='{pair}' and "
                                                         f"t.closed_by='{name}' order by t.id desc "
                                                         f"limit 1", header=False)[0]

                self.__send_notifications(pair=pair, close_time=current_time,
                                          fill_price=fill_price, interval=self.interval,
                                          event=event, action='CLOSE', usd_profit=profit,
                                          quote=quote_out, open_time=open_time, id=result)
            else:
                self.logger.error(f"TRADE: close margin long failed {name}: {pair}")
                return False

        del dbase
        return "closed"
