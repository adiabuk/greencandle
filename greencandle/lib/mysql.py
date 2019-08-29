#pylint: disable=undefined-variable, wrong-import-position, broad-except, no-member

"""
Push/Pull crypto signals and data to mysql
"""
import MySQLdb
from . import config
from .logger import getLogger, get_decorator


class Mysql():
    """
    Custom mysql object with methods to store and retrive given data
    """
    get_exceptions = get_decorator((Exception))

    def __init__(self, test=False, interval="15m"):
        self.host = config.database.host
        self.user = config.database.user
        self.password = config.database.password
        self.db = config.database.db
        self.db_test = config.database.db_test
        self.logger = getLogger(__name__, config.main.logging_level)

        self.connect(test=test)
        self.interval = interval
        self.logger.info("Starting Mysql with interval %s, test=%s", interval, test)

    @get_exceptions
    def connect(self, test=False):
        """
        Connect to Mysql DB
        """
        dbase_name = self.db_test if test else self.db
        self.dbase = MySQLdb.connect(host=self.host,
                                     user=self.user,
                                     passwd=self.password,
                                     db=dbase_name)
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
        cur.execute(command)
        self.dbase.commit()

    @get_exceptions
    def fetch_sql_data(self, query):
        """"
        Fetch SQL data for totals and return dict
        Args:
              String SQL select query
        Returns:
              tuple result
        """

        self.execute(cur, query)
        data = cursor.fetchall()
        return data

    @get_exceptions
    def run_sql_query(self, query):
        """
        Run a given mysql query (INSERT)
        Args:
              string query
        Returns:
              True/False success
        """
        cur = self.dbase.cursor()
        try:
            self.execute(cur, query)
        except NameError as exc:
            self.logger.critical("One or more expected variables not passed to DB %s", exc)
        except Exception:
            self.logger.critical("Error - unable to execute query %s", query)
        except MySQLdb.ProgrammingError:
            self.logger.critical("Syntax error in query: %s", query)

    @get_exceptions
    def delete_data(self):
        """
        Delete all data from trades table
        """
        self.logger.info("Deleting all trades from mysql")
        command = "delete from trades;"
        self.run_sql_query(command)

    @get_exceptions
    def insert_trade(self, pair, date, price, investment, total):
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

        self.logger.info("Buying %s using %s", pair, self.interval)
        command = """insert into trades (pair, buy_time, buy_price, investment, `interval`,
                     total) VALUES ("{0}", "{1}", "{2}", "{3}", "{4}", "{5}");""".format(pair, date,
                                                                                         float(price),
                                                                                         investment,
                                                                                         self.interval,
                                                                                         total)
        self.run_sql_query(command)

    @get_exceptions
    def get_quantity(self, pair):
        """
        Return quantity for a current open trade
        """
        command = """ select total from trades where sell_price
                      is NULL and `interval` = "{0}" and pair = "{1}" """.format(self.interval, pair)
        cur = self.dbase.cursor()
        self.execute(cur, command)

        row = [item[0] for item in cur.fetchall()]
        return row[0] if row else None # There should only be one open trade, so return first item

    @get_exceptions
    def get_trade_value(self, pair):
        """
        Return the value of an open trade for a given trading pair
        """

        command = """ select buy_price, total, buy_time from trades where sell_price
                      is NULL and `interval` = "{0}" and pair = "{1}" """.format(self.interval, pair)
        cur = self.dbase.cursor()
        self.execute(cur, command)

        row = [(item[0], item[1], item[2]) for item in cur.fetchall()]
        return row

    @get_exceptions
    def get_last_trades(self):
        """
        Get list of sell_time, buy_price, sell_price, and investment
        for each complete trade logged
        """
        cur = self.dbase.cursor()
        command = """ select sell_time, buy_price, sell_price, total from trades_{0} where
                      sell_price is NOT NULL; """.format(self.interval)

        self.execute(cur, command)
        return cur.fetchall()

    @get_exceptions
    def get_trades(self,):
        """
        Get a list of current open trades.  This is identified by a db record
        which has a buy price, but no sell price - ie. we haven"t sold it yet

        Args:
        Returns:
              a single list of pairs that we currently hold
        """
        cur = self.dbase.cursor()
        command = """ select pair from trades where sell_price is NULL and `interval`="{0}" """.format(self.interval)

        self.execute(cur, command)
        row = [item[0] for item in cur.fetchall()]
        return row

    @get_exceptions
    def update_trades(self, pair, sell_time, sell_price):
        """
        Update an existing trade with sell price
        """
        self.logger.info("Selling %s for %s", pair, self.interval)
        command = """update trades set sell_price={0},sell_time="{1}"
        where sell_price is NULL, interval="{2}" and pair="{3}" """.format(float(sell_price),
                                                                           sell_time,
                                                                           self.interval,
                                                                           pair)
        self.run_sql_query(command)

    @get_exceptions
    def insert_data(self, **kwargs):
        """
        Insert Data into DB
        Args:
              symbol
              event
              direction
              data
              difference
              resistance
              support
              buy
              sell
              market
              balance
        Returns:
              None
        """

        globals().update(kwargs)
        command = """INSERT INTO data (symbol, event, direction, data, difference,
                     resistance, support, buy, sell, market, balance) VALUES
                     ("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}");
                     """.format(symbol, event, direction, data, difference, resistance,
                                support, buy, sell, market, balance)
        self.run_sql_query(command)

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
                    command = """insert into balance (gbp, btc, usd, count, coin, exchange_id)
                                 values ("{0}", "{1}", "{2}", "{3}", "{4}", (select id from
                                 exchange where name="{5}"))""".format(data["GBP"], data["BTC"],
                                                                       data["USD"], data["count"],
                                                                       coin, exchange)
                except KeyError:
                    self.logger.critical(" ".join(["XXX", coin, exchange, "KEYERROR"]))
                    continue
                except IndexError:
                    self.logger.critical("Index error %s", exchange)
                    raise

                try:
                    self.run_sql_query(command)
                except NameError:
                    self.logger.error("One or more expected variables not passed to insert into DB")
