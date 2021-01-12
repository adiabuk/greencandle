#pylint: disable=undefined-variable, wrong-import-position, broad-except, no-member, logging-not-lazy

"""
Push/Pull crypto signals and data to mysql
"""
import MySQLdb
from . import config
from .binance_common import get_current_price
from .logger import get_logger, get_decorator

class Mysql():
    """
    Custom mysql object with methods to store and retrive given data
    """
    get_exceptions = get_decorator((Exception))

    def __init__(self, test=False, interval="15m"):
        self.host = config.database.db_host
        self.user = config.database.db_user
        self.password = config.database.db_password
        self.database = config.database.db_database
        self.logger = get_logger(__name__)

        self.connect()
        self.interval = interval
        self.logger.debug("Starting Mysql with interval %s, test=%s" % (interval, test))

    @get_exceptions
    def connect(self):
        """
        Connect to Mysql DB
        """
        self.dbase = MySQLdb.connect(host=self.host,
                                     user=self.user,
                                     passwd=self.password,
                                     db=self.database)
        self.cursor = self.dbase.cursor()

    @get_exceptions
    def __del__(self):
        try:
            self.dbase.close()
        except AttributeError:
            pass

    @get_exceptions
    def execute(self, cur, command):
        """
        Execute query on MYSQL DB - if fail, then try reconnecting and retry the operation
        """
        self.logger.debug("Running Mysql command: %s" % command)
        cur.execute(command)
        self.dbase.commit()

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
        self.execute(cur, query)
        output = list(cur.fetchall())
        description = list(list(column[0] for column in cur.description))
        if header:
            output.insert(0, description)
        return output

    @get_exceptions
    def run_sql_query(self, query):
        """
        Run a given mysql query (INSERT)
        Args:
              string query
        Returns:
              Number of affected rows
        """
        cur = self.dbase.cursor()
        try:
            self.execute(cur, query)
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
        self.run_sql_query(command)

    @get_exceptions
    def insert_trade(self, pair, date, price, base_amount, quote, borrowed='', multiplier=''):
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

        command = """insert into trades (pair, open_time, open_price, base_in, `interval`,
                     quote_in, name, borrowed, multiplier) VALUES ("{0}", "{1}", "{2}", "{3}", "{4}",
                     "{5}", "{6}", "{7}", "{8}");""".format(pair, date,
                                              '%.15f' % float(price),
                                              '%.15f' % float(base_amount),
                                              self.interval,
                                              quote, config.main.name, borrowed, multiplier)
        self.run_sql_query(command)

    @get_exceptions
    def get_recent_high(self, pair, date, months, max_perc):
        """
        Dertermine if we have completed a profitable trade for
        given pair within given amount of time

        Return True/False
        """
        command = ('select *  from profit where pair="{0}" and '
                   'close_time >= ("{1}" - interval "{2}" month) '
                   'and perc > "{3}"'.format(pair, date, months, max_perc))

        cur = self.dbase.cursor()
        self.execute(cur, command)
        return bool(cur.fetchall())

    @get_exceptions
    def get_quantity(self, pair):
        """
        Return quantity for a current open trade
        """
        command = ('select quote_in from trades where close_price '
                   'is NULL and `interval` = "{0}" and '
                   'pair = "{1}"'.format(self.interval, pair))
        cur = self.dbase.cursor()
        self.execute(cur, command)

        row = [item[0] for item in cur.fetchall()]
        return row[0] if row else None # There should only be one open trade, so return first item

    def get_last_close_time(self, pair):
        """
        Get time we closed last trade
        """
        cur = self.dbase.cursor()
        command = ('select close_time,pair from trades where pair="{0}" '
                   'and interval = "{1}" and close_time != "0000-00-00 00:00:00" '
                   'order by close_time desc LIMIT 1'.format(pair, interval))
        self.execute(cur, command)
        return cur.fetchall()

    @get_exceptions
    def get_trade_value(self, pair):
        """
        Return the value of an open trade for a given trading pair
        """

        command = ('select open_price, quote_in, open_time, base_in, borrowed from trades '
                   'where close_price is NULL and `interval` = "{0}" and '
                   'pair = "{1}"'.format(self.interval, pair))
        cur = self.dbase.cursor()
        self.execute(cur, command)

        row = [(item[0], item[1], item[2], item[3]) for item in cur.fetchall()]
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

        self.execute(cur, command)
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

        self.execute(cur, command)
        return cur.fetchall()

    @get_exceptions
    def update_trades(self, pair, close_time, close_price, quote, base_out,
                      name=None, drawdown='NULL'):
        """
        Update an existing trade with sell price
        """
        job_name = name if name else config.main.name
        command = """update trades set close_price={0},close_time="{1}", quote_out="{2}",
        base_out="{3}", closed_by="{6}", drawdown_perc=abs(round({7},1)) where close_price is
        NULL and `interval`="{4}" and pair="{5}" and (name like "{6}" or
        name like "api") """.format('%.15f' % float(close_price),
                                    close_time,
                                    '%.15f' % float(quote),
                                    '%.15f' % float(base_out),
                                    self.interval,
                                    pair,
                                    job_name, drawdown)
        result = self.run_sql_query(command)
        if result != 1:
            self.logger.critical("Query affected %s rows" % result)

    def get_active_trades(self):
        """
        Get current active trades and store in active_trades table with current price
        """

        self.run_sql_query("delete from open_trades")
        trades = self.fetch_sql_data("select pair, open_time, open_price, name from trades where "
                                     "close_price is NULL", header=False)
        for trade in trades:
            try:
                pair, open_time, open_price, name = trade
                current_price = get_current_price(pair)
                perc = 100 * (float(current_price) - float(open_price)) / float(open_price)
                insert = ('insert into open_trades (pair, open_time, open_price, current_price, '
                          'perc, name) VALUES ("{0}", "{1}", "{2}", "{3}", "{4}", "{5}")'
                          .format(pair, open_time, open_price, current_price, perc, name))

                self.run_sql_query(insert)
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
                    self.run_sql_query(command)
                except NameError:
                    self.logger.error("One or more expected variables not passed to insert into DB")
