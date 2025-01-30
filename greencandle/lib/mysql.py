#pylint: disable=broad-except,no-member,too-many-arguments,too-many-locals,too-many-public-methods

"""
Push/Pull crypto signals and data to mysql
"""
import datetime
import MySQLdb
from greencandle.lib import config
from greencandle.lib.objects import AttributeDict
from greencandle.lib.binance_accounts import get_local_price
from greencandle.lib.balance_common import get_base, get_quote
from greencandle.lib.logger import get_logger, exception_catcher

class Mysql():
    """
    Custom mysql object with methods to store and retrive given data
    """
    get_exceptions = exception_catcher((Exception))

    def __init__(self, test=False, interval="15m", host=None, port=3306):
        self.creds = AttributeDict()
        self.port = port
        self.creds.host = host if host else config.database.db_host
        self.creds.user = config.database.db_user
        self.creds.password = config.database.db_password
        self.creds.database = config.database.db_database
        self.logger = get_logger(__name__)

        self.__connect()
        self.interval = interval
        self.test = test
        self.logger.debug("Starting Mysql with interval %s, test=%s", interval, test)

    @get_exceptions
    def __connect(self):
        """
        Connect to Mysql DB
        """
        self.dbase = MySQLdb.connect(host=self.creds.host,
                                     port=self.port,
                                     user=self.creds.user,
                                     passwd=self.creds.password,
                                     db=self.creds.database)
        self.cursor = self.dbase.cursor()

    @get_exceptions
    def __del__(self):
        try:
            self.dbase.close()
        except AttributeError:
            pass

    def __execute(self, cur, command):
        """
        Execute query on MYSQL DB
        """
        self.logger.debug("Running Mysql command: %s", command)
        try:
            cur.execute(command)
        except MySQLdb.ProgrammingError:
            self.logger.critical("Error running SQL command %s", command)
            return

        self.dbase.commit()

    @get_exceptions
    def run_sql_statement(self, command):
        """
        run sql statement without results
        """
        cur = self.dbase.cursor()
        self.__execute(cur, command)

    @get_exceptions
    def delete_table_contents(self, table_name):
        """
        delete contents of given table
        """

        self.run_sql_statement(f'delete from {table_name}')

    @get_exceptions
    def insert_extra_loan(self, symbol, borrowed, borrowed_usd):
        """
        Insert extra loan into db
        """
        command = (f"insert into extra_loans (symbol, borrowed, borrowed_usd) values "
                   f"('{symbol}', '{borrowed}', '{borrowed_usd}')")

        self.__run_sql_query(command, get_id=False)

    @get_exceptions
    def get_extra_loan_amt(self, symbol):
        """
        Get amount borrowed for a specific symbol
        """
        command = (f"select borrowed from extra_loans where date_removed is null and "
                   f"symbol = '{symbol}' order by date_added desc limit 1")
        result = self.fetch_sql_data(command, header=False)
        return float(result[0][0]) if result else 0

    @get_exceptions
    def get_extra_loans(self):
        """
        Get list of symbols with have loans but awaiting trade
        """
        raw_list = self.fetch_sql_data('select symbol from extra_loans where date_removed is null',
                                       header=False)
        return [sub for item in raw_list for sub in item] # flatten list of lists

    def update_extra_loan(self, symbol):
        """
        update extra loan record with date
        """
        command = (f"update extra_loans set date_removed=now() where symbol='{symbol}' and "
                   "date_removed is NULL order by date_added desc")
        self.__run_sql_query(command, get_id=False)

    @get_exceptions
    def fetch_sql_data(self, query, header=True):
        """"
        Fetch SQL data for totals and return dict
        Args:
              String SQL select query
        Returns:
              tuple result
        """

        cur = self.dbase.cursor()
        self.__execute(cur, query)
        output = list(cur.fetchall())
        description = list(list(column[0] for column in cur.description))
        if header:
            output.insert(0, description)
        # turn list of tuple into list of lists
        res = [list(ele) for ele in output]
        return res

    @get_exceptions
    def __run_sql_query(self, query, get_id=False):
        """
        Run a given mysql query (INSERT)
        Args:
              string query
        Returns:
              Number of affected rows
        """
        cur = self.dbase.cursor()
        try:
            self.__execute(cur, query)
            return cur.lastrowid if get_id else cur.rowcount
        except NameError as exc:
            self.logger.critical("One or more expected variables not passed to db %s", exc)
            return False
        except MySQLdb.ProgrammingError:
            self.logger.critical("Syntax error in query: %s", query)
            return False
        except Exception:
            self.logger.critical("Error - unable to execute query: %s", query)
            return False

        return True

    @get_exceptions
    def delete_data(self):
        """
        Delete all data from trades table
        """
        self.logger.info("Deleting all trades from mysql")
        command = "delete from trades;"
        self.__run_sql_query(command)

    @get_exceptions
    def insert_trade(self, pair, date, price, quote_amount, base_amount, borrowed='0',
                     borrowed_usd=0, divisor='0', direction='', symbol_name=None,
                     commission=None, order_id=0, comment=''):
        """
        Insert new trade into DB
        Args:
              pair: traiding pair
              date: date/time of trade
              price: current price of pair
              investment: amount invested in gbp
              total:

        Returns:
              None
        """
        usd_rate, gbp_rate = self.get_rates(symbol_name)
        command = (f'insert into trades (pair, open_time, open_price, base_in, `interval`, '
                   f'quote_in, name, borrowed, borrowed_usd, divisor, direction, open_usd_rate, '
                   f'open_gbp_rate, comm_open, open_order_id, comment) VALUES ("{pair}", "{date}", '
                   f'trim("{float(price):.15f}")+0, "{float(base_amount):.15f}", '
                   f'"{self.interval}", "{quote_amount}", "{config.main.name}", "{borrowed}", '
                   f'"{borrowed_usd}", "{divisor}", "{direction}", "{usd_rate}", "{gbp_rate}", '
                   f'"{commission}", "{order_id}", "{comment}")')

        result = self.__run_sql_query(command, get_id=True)

        return result

    def get_open_trades(self, name_filter="", direction_filter="", pair_filter="",header=False):
        """
        get_details of open trades
        """
        query = (f"select open_time, `interval`, pair, name, open_price, direction, quote_in from "
                 f"trades where close_price is null and name like '%{name_filter}%' and "
                 f"pair like '%{pair_filter}%' and `direction` like '%{direction_filter}%';")
        raw = self.fetch_sql_data(query, header=header)

        return raw if raw else []

    def insert_api_trade(self, **kwargs):
        """
        archive data received from api-router
        """
        kwargs = AttributeDict(kwargs)
        command = f"""insert into api_requests (pair, text, action, price, strategy) VALUES
                     ("{kwargs.pair}", "{kwargs.text}", "{kwargs.action}",
                     "{kwargs.get('price', 'N/A')}", "{kwargs.strategy}")"""
        result = self.__run_sql_query(command)
        return result == 1

    @get_exceptions
    def get_recent_high(self, pair, date, months, max_perc):
        """
        Dertermine if we have completed a profitable trade for
        given pair within given amount of time

        Return True/False
        """
        command = (f'select * from profit where pair="{pair}" and name="{config.main.name}" '
                   f'and close_time >= ("{date}" - interval "{months}" month) ' 'and perc '
                   f'> "{max_perc}" and direction="{config.main.trade_direction}"')

        cur = self.dbase.cursor()
        self.__execute(cur, command)
        return bool(cur.fetchall())

    @get_exceptions
    def get_complete_commission(self):
        """
        Get commission value for open and close trade
        """
        command = 'select commission()'

        cur = self.dbase.cursor()
        self.__execute(cur, command)

        row = [item[0] for item in cur.fetchall()]
        return float(row[0]) if row else None # There should only be one row, so return first item

    @get_exceptions
    def get_quantity(self, pair):
        """
        Return quantity for a current open trade
        """
        command = (f'select base_in from trades where close_price '
                   f'is NULL and `interval` = "{self.interval}" and '
                   f'pair = "{pair}" and name="{config.main.name}" LIMIT 1')

        cur = self.dbase.cursor()
        self.__execute(cur, command)

        row = [item[0] for item in cur.fetchall()]
        return row[0] if row else None # There should only be one open trade, so return first item

    @get_exceptions
    def get_var_value(self, name):
        """
        get variable from db
        """
        query = f"select get_var('{name}')"
        result = self.fetch_sql_data(query, header=False)[0][0]
        return result

    @get_exceptions
    def get_trade_value(self, pair):
        """
        Return details for calculating value of an open trade for a given trading pair
        """

        command = (f'select open_price, quote_in, open_time, base_in, borrowed, borrowed_usd '
                   f'from trades where close_price is NULL and `interval` = "{self.interval}" '
                   f'and pair = "{pair}" and name ="{config.main.name}" '
                   f'and direction="{config.main.trade_direction}"')

        cur = self.dbase.cursor()
        self.__execute(cur, command)

        row = [(item[0], item[1], item[2], item[3], item[4], item[5]) for item in cur.fetchall()]
        return row if row else [[None] * 6]

    @get_exceptions
    def get_last_trades(self):
        """
        Get list of close_time, open_price, close_price, and investment
        for each complete trade logged
        """
        cur = self.dbase.cursor()
        command = (f'select close_time, open_price, close_price, quote_in from trades where '
                   f'`interval` = "{self.interval}" and close_price is NOT NULL')

        self.__execute(cur, command)
        return cur.fetchall()

    @get_exceptions
    def get_trades(self, direction=''):
        """
        Get a list of current open trades.  This is identified by a db record
        which has a open price, but no close price - ie. we haven"t sold it yet

        Args:
        Returns:
              a single list of pairs that we currently hold with the open time
        """
        cur = self.dbase.cursor()
        command = (f'select pair, open_time, open_price from trades where close_price is NULL and '
                   f'`interval`="{self.interval}" and name in ("{config.main.name}","api") and '
                   f'direction like "%{direction}%"')

        self.__execute(cur, command)
        return cur.fetchall()

    def get_rates(self, quote):
        """
        Get current rates
        return tupple of usd_rate and gbp_rate
        """
        if self.test:
            return (1, 1)
        usd_rate = get_local_price(quote + 'USDT') if quote != 'USDT' else 1
        gbp_rate = usd_rate / get_local_price('GBPUSDT')
        return (usd_rate, gbp_rate)

    @get_exceptions
    def update_trades(self, pair, close_time, close_price, quote, base_out,
                      name=None, drawdown=0, drawup=0, symbol_name=None, commission=None,
                      order_id=0, comment=''):
        """
        Update an existing trade with close price
        """
        usd_rate, gbp_rate = self.get_rates(symbol_name)
        job_name = name if name else config.main.name
        query = f"""select id from trades where close_price is NULL and
                   `interval`="{self.interval}" and pair="{pair}" and (name="{job_name}"
                   or name like "api") and direction="{config.main.trade_direction}"
                   ORDER BY ID ASC LIMIT 1"""
        try:
            trade_id = self.fetch_sql_data(query, header=False)[0][0]
        except IndexError:
            self.logger.critical("No open trade matching criteria to close: %s", query)
            return None

        command = f"""update trades set close_price=trim({float(close_price):.15f})+0,
                      close_time="{close_time}", quote_out="{quote}",
                      base_out="{float(base_out):.15f}", closed_by="{job_name}",
                      drawdown_perc=abs(round({drawdown},1)), drawup_perc=abs(round({drawup},1)),
                      close_usd_rate="{usd_rate}", close_gbp_rate="{gbp_rate}",
                      comm_close="{commission}", close_order_id="{order_id}", comment="{comment}"
                      where id = "{trade_id}"
                   """

        self.__run_sql_query(command)

        return trade_id

    @get_exceptions
    def get_todays_profit(self):
        """
        Get today's profit perc so far
        Returns float
        """
        command = ('select sum(usd_profit), sum(usd_net_profit), avg(perc), '
                   'avg(net_perc), sum(perc), sum(net_perc), count(*) '
                   'from profit where date(close_time) = date(NOW())')
        row = self.fetch_sql_data(command, header=False)
        return row[0] if row else [None] * 7

    def trade_in_context(self, pair, name, direction):
        """
        Check if a trade exists for given pair, name, and direction
        """

        query = (f'select * from trades where pair="{pair}" and name="{name}" and '
                 f'direction="{direction}" and close_price is null')
        result = self.fetch_sql_data(query, header=False)
        return bool(result)

    @get_exceptions
    def get_last_hour_profit(self, date=None, hour=None):
        """
        Get profit for the last completed hour
        """
        hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
        date = date if date else hour_ago.strftime("%Y-%m-%d")
        hour = hour if hour else hour_ago.strftime("%H")

        command = (f'select COALESCE(total_perc,0) total_perc, '
                   f'COALESCE(total_net_perc,0) total_net_perc, '
                   f'COALESCE(avg_perc,0) avg_perc, '
                   f'COALESCE(avg_net_perc,0) avg_net_perc, '
                   f'COALESCE(usd_profit,0) usd_profit, '
                   f'COALESCE(usd_net_profit,0) usd_net_profit, '
                   f'COALESCE(num_trades,0) num_trades '
                   f'from profit_hourly where '
                   f'date="{date}" and hour="{hour}"')
        result = self.fetch_sql_data(command, header=False)
        output = [float(item) for item in result[0]] if result else [None] * 7
        output.append(hour)
        # returns total_perc, total_net_perc, avg_perc, avg_net_perc, usd_profit, usd_net_profit,
        # num_hour, count
        # + hour in list
        return output

    @get_exceptions
    def get_current_borrowed(self, pair, account):
        """
        Get amount borrowed in current scope
        """
        command = (f'select pair, borrowed, direction from trades '
                   f'where pair like "%{pair}%" and name like "%{account}%" '
                   f'and close_price is NULL')

        cur = self.dbase.cursor()
        self.__execute(cur, command)

        rows = cur.fetchall()
        return rows if rows else ()

    @get_exceptions
    def get_main_open_assets(self):
        """
        get unique set of assets from open trade pairs which are likely
        to a loan against them depending on trade direction
        base asset if short, quote asset if long
        """
        open_set = set()
        open_trades = self.fetch_sql_data('select pair, direction from trades where '
                                          'close_price is null', header=False)
        # get unique set of pairs with open trades
        # get assets from pairs, base if short, quote if long
        for pair, direction in open_trades:
            if direction == 'short':
                open_set.add(get_base(pair))
            else:
                open_set.add(get_quote(pair))
        return open_set

    @get_exceptions
    def add_commission_payment(self, asset, asset_amt, usd_amt, gbp_amt):
        """
        Insert commission payment into db
        """

        insert = (f"insert into commission_paid (asset, asset_amt, usd_amt, gbp_amt) VALUES "
                  f"('{asset}', '{asset_amt}', '{usd_amt}', '{gbp_amt}')")

        self.__run_sql_query(insert)

    @get_exceptions
    def insert_balance(self, balances):
        """
        Insert balance in GBP/BTC/USD into balance table for coinbase & binance
        Args:
              dict of balances
        Returns:
              None
        """

        for exchange, values in balances.items():
            for coin, data in values.items():
                try:
                    command = (f'insert into balance (gbp, btc, usd, count, coin, exchange_id) '
                               f'values ("{data["GBP"]}", "{data["BTC"]}", "{data["USD"]}", '
                               f'"{data["count"]}", "{coin}", (select id from '
                               f'exchange where name="{exchange}"))')
                except KeyError:
                    self.logger.debug(" ".join(["Unable to find coin:", coin,
                                               exchange, "KEYERROR"]))
                    continue
                except IndexError:
                    self.logger.critical("Index error %s", exchange)
                    raise

                try:
                    self.__run_sql_query(command)
                except NameError:
                    self.logger.critical("Expected variables not passed to insert into db")
