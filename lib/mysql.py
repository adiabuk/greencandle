#pylint: disable=undefined-variable, wrong-import-position, broad-except

"""
Push/Pull crypto signals and data to mysql
"""
import os
import sys
import operator
import MySQLdb
import MySQLdb.cursors
import binance

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)

from lib.config import get_config
from lib.logger import getLogger, get_decorator

HOST = get_config("database")["host"]
USER = get_config("database")["user"]
PASSWORD = get_config("database")["password"]
DB = get_config("database")["db"]
DB_TEST = get_config("database")["db_test"]
LOGGER = getLogger(__name__)

class Mysql(object):
    """
    Custom mysql object with methods to store and retrive given data
    """
    get_exceptions = get_decorator((Exception))

    def __init__(self, test=False, interval="15m"):
        self.connect(test=test)
        self.interval = interval
        LOGGER.debug("Starting Mysql with interval %s, test=%s", interval, test)

    @get_exceptions
    def connect(self, test=False):
        """
        Connect to Mysql DB
        """
        if test:
            dbase_name = DB_TEST
        else:
            dbase_name = DB
        self.dbase = MySQLdb.connect(host=HOST,
                                     user=USER,
                                     passwd=PASSWORD,
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
    def get_buy(self):
        """
        Get list of pairs which have just changed from SELL, to BUY and order by strength,
        return ordered tuple.  We look at pairs which have just switched from SELL to BUY
        to catch it at the beginning of an upward trend.  If the state is already BUY then we
        have likely missed the train, so we pass.
        Args:
              None
        Returns:
              sorted tuple each containing pair, score, current price
        """
        LOGGER.debug("Finding symbols to buy")
        potential_buys = self.get_changes()
        sorted_buys = sorted(potential_buys.items(), key=operator.itemgetter(1))[::-1]

        return sorted_buys

    @get_exceptions
    def get_sell(self):
        """
        From list of current pair holdings list all which are currently in SELL regardless of
        score.  We are not just looking for pairs that have just switched, incase we miss the
        trigger ordered tuple
        Args:
              None
        Returns:
              None
        """

        current_holdings = self.get_trades()
        command = """select t1.pair from (select pair, total, max(ctime) AS MaxCreated
                     from action_totals group by pair) t2 join action_totals t1 on
                     t2.pair = t1.pair and t2.MaxCreated = t1.ctime and
                     t1.total < 1 and t1.total = t2.total ;"""

        cur = self.dbase.cursor()
        self.execute(cur, command)
        all_sell = [item[0] for item in cur.fetchall()]

        current_sell = [item for item in current_holdings if item in all_sell]
        return current_sell

    @get_exceptions
    def get_changes(self):
        """
        Get changes of status from BUY to SELL by running a query that compares current value to
        previous value
        Args:
              None
        Returns:
              dict of values.  Keys: pair, ctime, total, gt
              where gt indicates the strength of the BUY signal
        """
        # FIXME: make select match docstring returns
        command = """ select s1.pair as pair, s1.ctime AS ctime1, s2.ctime as ctime2,
                      s1.total AS total1, s2.total as total2,
                      ((s1.total >= 0) and (s2.total <= 0)) AS gt
                      from (action_totals s1 left join action_totals s2 on
                      ((s1.pair = s2.pair))) where (
                      (s1.total <> s2.total) and
                      ((s1.total > 0) and (s2.total <0)) and
                      (s1.ctime > (now() - interval 5 minute)) and
                      (s2.ctime < now() - interval 15 minute)); """
        return self.fetch_sql_data(command)

    @get_exceptions
    def fetch_sql_data(self, query):
        """"
        Fetch SQL data for totals and return dict
        Args:
              String SQL select query
        Returns:
              dict of tuples.  where key is pair name containing a tuple of total and current price)
        """

        di = {}
        prices = binance.prices()
        with self.cursor(MySQLdb.cursors.DictCursor) as cursor:
            self.execute(cur, query)
            data = cursor.fetchall()
            for record in data:
                di[record["pair"]] = record["total1"], prices[record["pair"]]

        return di

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
        except NameError as e:
            LOGGER.critical("One or more expected variables not passed to DB %s", e)
        except Exception:
            LOGGER.critical("AMROX6 - unable to execute query %s", query)

    @get_exceptions
    def delete_data(self):
        """
        Delete all data from trades table
        """
        LOGGER.info("Deleting all trades from mysql")
        command = "delete from trades_{0};".format(self.interval)
        command2 = "delete from actions;"
        self.run_sql_query(command)
        self.run_sql_query(command2)

    @get_exceptions
    def clean_stale(self):
        """
        Delete stale records from actions and action_totals db tables - any records older than 30
        minutes
        Args:
              None
        Returns:
              None
        """

        LOGGER.info("Cleaning stale data from mysql")
        command1 = "delete from action_totals where ctime < NOW() - INTERVAL 30 MINUTE;"
        command2 = "delete from actions where ctime < NOW() - INTERVAL 30 MINUTE;"
        self.run_sql_query(command1)
        self.run_sql_query(command2)

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

        LOGGER.info("AMROX5 Buying %s using %s", pair, self.interval)
        command = """insert into trades_{0} (pair, buy_time, buy_price, investment,
                     total) VALUES ("{1}", "{2}", "{3}", "{4}", "{5}");""".format(self.interval,
                                                                                  pair, date,
                                                                                  float(price),
                                                                                  investment,
                                                                                  total)
        self.run_sql_query(command)

    @get_exceptions
    def get_quantity(self, pair):
        """
        Return quantity for a current open trade
        """
        command = """ select total from trades_{0} where sell_price
                      is NULL and pair = "{1}" """.format(self.interval, pair)
        cur = self.dbase.cursor()
        self.execute(cur, command)

        row = [item[0] for item in cur.fetchall()]
        LOGGER.debug("%s %s", command, row)
        return row[0] if row else None # There should only be one open trade, so return first item

    @get_exceptions
    def get_trade_value(self, pair):
        """
        Return the value of an open trade for a given trading pair
        """

        command = """ select buy_price from trades_{0} where sell_price
                      is NULL and pair = "{1}" """.format(self.interval, pair)
        cur = self.dbase.cursor()
        self.execute(cur, command)

        row = [item[0] for item in cur.fetchall()]
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
        command = """ select pair from trades_{0} where sell_price is NULL """.format(self.interval)

        self.execute(cur, command)
        row = [item[0] for item in cur.fetchall()]
        return row

    @get_exceptions
    def update_trades(self, pair, sell_time, sell_price):
        """
        Update an existing trade with sell price
        """
        LOGGER.info("Selling %s for %s", pair, self.interval)
        command = """update trades_{0} set sell_price={1},sell_time="{2}"
        where sell_price is NULL and pair="{3}" """.format(self.interval,
                                                           float(sell_price), sell_time, pair)
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
                    LOGGER.critical(" ".join(["XXX", coin, exchange, "KEYERROR"]))
                    continue
                except IndexError:
                    LOGGER.critical("Index error %s", exchange)
                    raise

                try:
                    self.run_sql_query(command)
                except NameError:
                    LOGGER.error("One or more expected variables not passed to insert into DB")

    @get_exceptions
    def insert_action_totals(self):
        """
        Get recent coin actions from actions table, sum totals and insert into action_totals table
        Args:
              None
        Returns:
              None
        """

        LOGGER.debug("Inserting Totals")
        command = """ INSERT INTO action_totals (pair, total) select pair, SUM(action) as total from
        recent_actions group by pair order by total;"""
        self.run_sql_query(command)

    @get_exceptions
    def insert_actions(self, **kwargs):
        """
        Insert actions into actions table
        Args:
              pair (string pairname)
              indicator (eg. RSI, Supertrend)
              value: value of indicator/oscilator
              action: 0/1/-1 for HOLD, BUY,SELL (used to sum totals later)
        Returns:
              None
        """

        globals().update(kwargs)

        command = """INSERT INTO actions (pair, indicator, value, action)
                     VALUES ("{0}","{1}","{2}","{3}");""".format(pair, indicator, value, action)

        self.run_sql_query(command)
