#pylint: disable=undefined-variable, wrong-import-position, broad-except, no-member, logging-not-lazy

"""
Push/Pull crypto signals and data to mysql
"""
import MySQLdb
from currency_converter import CurrencyConverter
from binance import binance
from . import config
from .binance_common import get_current_price
from .common import AttributeDict
from .logger import get_logger, get_decorator

class Mysql():
    """
    Custom mysql object with methods to store and retrive given data
    """
    get_exceptions = get_decorator((Exception))

    def __init__(self, test=False, interval="15m"):
        self.creds = AttributeDict()
        self.creds.host = config.database.db_host
        self.creds.user = config.database.db_user
        self.creds.password = config.database.db_password
        self.creds.database = config.database.db_database
        self.logger = get_logger(__name__)

        self.__connect()
        self.interval = interval
        self.logger.debug("Starting Mysql with interval %s, test=%s" % (interval, test))

    @get_exceptions
    def __connect(self):
        """
        Connect to Mysql DB
        """
        self.dbase = MySQLdb.connect(host=self.creds.host,
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

    @get_exceptions
    def __execute(self, cur, command):
        """
        Execute query on MYSQL DB - if fail, then try reconnecting and retry the operation
        """
        self.logger.debug("Running Mysql command: %s" % command)
        cur.execute(command)
        self.dbase.commit()

    @get_exceptions
    def run_sql_statement(self, command):
        """
        run sql statement without results
        """
        cur = self.dbase.cursor()
        self.__execute(cur, command)


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
        return output

    @get_exceptions
    def __run_sql_query(self, query):
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
            return cur.rowcount
        except NameError as exc:
            self.logger.critical("One or more expected variables not passed to DB %s" % exc)
        except Exception:
            self.logger.critical("Error - unable to execute query %s" % query)
        except MySQLdb.ProgrammingError:
            self.logger.critical("Syntax error in query: %s" % query)

    @get_exceptions
    def delete_data(self):
        """
        Delete all data from trades table
        """
        self.logger.info("Deleting all trades from mysql")
        command = "delete from trades;"
        self.__run_sql_query(command)

    @get_exceptions
    def insert_trade(self, pair, date, price, base_amount, quote, borrowed='', multiplier='',
                     direction='', base=None):
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
        usd_rate, gbp_rate = self.get_rates(base)
        command = """insert into trades (pair, open_time, open_price, base_in, `interval`,
                     quote_in, name, borrowed, multiplier, direction, open_usd_rate, open_gbp_rate)
                     VALUES ("{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}", "{7}", "{8}", "{9}",
                     "{10}", "{11}" ); """.format(pair, date, '%.15f' % float(price),
                                                  '%.15f' % float(base_amount),
                                                  self.interval,
                                                  quote, config.main.name, borrowed, multiplier,
                                                  direction, usd_rate, gbp_rate)
        result = self.__run_sql_query(command)
        return result == 1


    @get_exceptions
    def get_recent_high(self, pair, date, months, max_perc):
        """
        Dertermine if we have completed a profitable trade for
        given pair within given amount of time

        Return True/False
        """
        command = ('select * from profit where pair="{0}" and name="{1}" and close_time '
                   '>= ("{2}" - interval "{3}" month) ' 'and perc '
                   '> "{3}"'.format(pair, date, months, max_perc))

        cur = self.dbase.cursor()
        self.__execute(cur, command)
        return bool(cur.fetchall())

    @get_exceptions
    def get_quantity(self, pair):
        """
        Return quantity for a current open trade
        """
        command = ('select quote_in from trades where close_price '
                   'is NULL and `interval` = "{0}" and '
                   'pair = "{1}" and name="{2}" LIMIT 1'
                   .format(self.interval, pair, config.main.name))

        cur = self.dbase.cursor()
        self.__execute(cur, command)

        row = [item[0] for item in cur.fetchall()]
        return row[0] if row else None # There should only be one open trade, so return first item

    @get_exceptions
    def get_trade_value(self, pair):
        """
        Return the value of an open trade for a given trading pair
        """

        command = ('select open_price, quote_in, open_time, base_in, borrowed from trades '
                   'where close_price is NULL and `interval` = "{0}" and '
                   'pair = "{1}" and name ="{2}"'.format(self.interval, pair, config.main.name))
        cur = self.dbase.cursor()
        self.__execute(cur, command)

        row = [(item[0], item[1], item[2], item[3], item[4]) for item in cur.fetchall()]
        return row

    @get_exceptions
    def get_last_trades(self):
        """
        Get list of close_time, open_price, close_price, and investment
        for each complete trade logged
        """
        cur = self.dbase.cursor()
        command = ('select close_time, open_price, close_price, quote_in from trades where '
                   '`interval` = "{0}" and close_price is NOT NULL'.format(self.interval))

        self.__execute(cur, command)
        return cur.fetchall()

    @get_exceptions
    def get_trades(self):
        """
        Get a list of current open trades.  This is identified by a db record
        which has a buy price, but no sell price - ie. we haven"t sold it yet

        Args:
        Returns:
              a single list of pairs that we currently hold with the buy time
        """
        cur = self.dbase.cursor()
        command = ('select pair, open_time from trades where close_price is NULL and '
                   '`interval`="{0}" ' 'and name in ("{1}","api")'
                   .format(self.interval, config.main.name))

        self.__execute(cur, command)
        return cur.fetchall()

    @staticmethod
    def get_rates(base):
        """
        Get current rates
        return tupple of usd_rate and gbp_rate
        """
        currency = CurrencyConverter()
        usd_rate = binance.prices()[base + 'USDT'] if base != 'USDT' else "1"
        gbp_rate = currency.convert(usd_rate, 'USD', 'GBP')

        return (usd_rate, gbp_rate)

    @get_exceptions
    def update_trades(self, pair, close_time, close_price, quote, base_out,
                      name=None, drawdown=0, drawup=0, base=None):
        """
        Update an existing trade with sell price
        """
        usd_rate, gbp_rate = self.get_rates(base)
        job_name = name if name else config.main.name
        command = """update trades set close_price={0},close_time="{1}",
        quote_out="{2}", base_out="{3}", closed_by="{6}", drawdown_perc=abs(round({7},1)),
        drawup_perc=abs(round({8},1)), close_usd_rate="{9}", close_gbp_rate="{10}" where close_price is
        NULL and `interval`="{4}" and pair="{5}" and (name = "{6}" or
        name like "api") and (SELECT @uids:= CONCAT_WS(",", id, @uids)) ORDER BY id LIMIT 1""" \
        .format('%.15f' % float(close_price),
                close_time, quote,
                '%.15f' % float(base_out),
                self.interval, pair, job_name, drawdown,
                drawup, usd_rate, gbp_rate)
        self.__run_sql_query("SET @uids := null;")
        result = self.__run_sql_query(command)
        if result != 1:
            self.logger.critical("Query affected %s rows: %s" % (result, command))
        return  self.fetch_sql_data("SELECT @uids;", header=False)[0][0].decode()

    def get_active_trades(self):
        """
        Get current active trades and store in active_trades table with current price
        """

        self.__run_sql_query("delete from open_trades")
        trades = self.fetch_sql_data("select pair, open_time, open_price, name, `interval`, "
                                     "open_usd_rate*base_in as usd_quantity from "
                                     "trades where close_price is NULL or close_price=''",
                                     header=False)
        for trade in trades:
            try:
                pair, open_time, open_price, name, interval, usd_quantity = trade
                current_price = get_current_price(pair)
                perc = 100 * (float(current_price) - float(open_price)) / float(open_price)
                insert = ('insert into open_trades (pair, open_time, open_price, current_price, '
                          'perc, name, `interval`, usd_quantity) VALUES ("{0}", "{1}", "{2}", '
                          '"{3}", "{4}", "{5}", "{6}", "{7}")'.format(pair, open_time, open_price,
                                                                      current_price, perc, name,
                                                                      interval, usd_quantity))

                self.__run_sql_query(insert)
            except ZeroDivisionError:
                self.logger.critical("%s has a zero buy price, unable to calculate percentage"
                                     % pair)


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
                    command = ('insert into balance (gbp, btc, usd, count, coin, exchange_id) '
                               'values ("{0}", "{1}", "{2}", "{3}", "{4}", (select id from '
                               'exchange where name="{5}"))'.format(data["GBP"], data["BTC"],
                                                                    data["USD"], data["count"],
                                                                    coin, exchange))
                except KeyError:
                    self.logger.critical(" ".join(["XXX", coin, exchange, "KEYERROR"]))
                    continue
                except IndexError:
                    self.logger.critical("Index error %s" % exchange)
                    raise

                try:
                    self.__run_sql_query(command)
                except NameError:
                    self.logger.error("One or more expected variables not passed to insert into DB")
