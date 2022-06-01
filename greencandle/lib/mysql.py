#pylint: disable=undefined-variable, wrong-import-position, broad-except, no-member, logging-not-lazy

"""
Push/Pull crypto signals and data to mysql
"""
import datetime
from binance.binance import Binance
import MySQLdb
from . import config
from .binance_common import get_current_price
from .common import AttributeDict, format_usd
from .logger import get_logger, exception_catcher

class Mysql():
    """
    Custom mysql object with methods to store and retrive given data
    """
    get_exceptions = exception_catcher((Exception))

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
    def insert_trade(self, pair, date, price, quote_amount, base_amount, borrowed='0',
                     multiplier='0', direction='', symbol_name=None, commission=None):
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
        command = """insert into trades (pair, open_time, open_price, base_in, `interval`,
                     quote_in, name, borrowed, multiplier, direction, open_usd_rate, open_gbp_rate,
                     comm_open) VALUES ("{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}", "{7}",
                     "{8}", "{9}", "{10}", "{11}", "{12}");
                   """.format(pair, date, '%.15f' % float(price), '%.15f' % float(base_amount),
                              self.interval, quote_amount, config.main.name, borrowed,
                              multiplier, direction, usd_rate, gbp_rate, commission)

        result = self.__run_sql_query(command)
        return result == 1

    def insert_api_trade(self, **kwargs):
        """
        archive data received from api-router
        """
        kwargs = AttributeDict(kwargs)
        command = """insert into api_requests (pair, text, action, price, strategy) VALUES
                     ('{0}', '{1}', '{2}', '{3}', '{4}')""".format(kwargs.pair,
                                                                   kwargs.text,
                                                                   kwargs.action,
                                                                   kwargs.get('price', 'N/A'),
                                                                   kwargs.strategy)
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
        command = ('select base_in from trades where close_price '
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
        Return details for calculating value of an open trade for a given trading pair
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
    def get_rates(quote):
        """
        Get current rates
        return tupple of usd_rate and gbp_rate
        """
        client = Binance()
        usd_rate = client.prices()[quote + 'USDT'] if quote != 'USDT' else "1"
        gbp_rate = float(usd_rate)/float(client.prices()['GBPUSDT'])
        return (usd_rate, gbp_rate)

    @get_exceptions
    def update_trades(self, pair, close_time, close_price, quote, base_out,
                      name=None, drawdown=0, drawup=0, symbol_name=None, commission=None):
        """
        Update an existing trade with sell price
        """
        usd_rate, gbp_rate = self.get_rates(symbol_name)
        job_name = name if name else config.main.name
        command = """update trades set close_price={0},close_time="{1}",
        quote_out="{2}", base_out="{3}", closed_by="{6}", drawdown_perc=abs(round({7},1)),
        drawup_perc=abs(round({8},1)), close_usd_rate="{9}", close_gbp_rate="{10}",
        comm_close="{11}" where close_price is
        NULL and `interval`="{4}" and pair="{5}" and (name = "{6}" or
        name like "api") and (SELECT @uids:= CONCAT_WS(",", id, @uids)) ORDER BY id LIMIT 1""" \
        .format('%.15f' % float(close_price),
                close_time, quote,
                '%.15f' % float(base_out),
                self.interval, pair, job_name, drawdown,
                drawup, usd_rate, gbp_rate, str(commission))
        self.__run_sql_query("SET @uids := null;")
        result = self.__run_sql_query(command)
        if result != 1:
            self.logger.critical("Query affected %s rows: %s" % (result, command))
        return  self.fetch_sql_data("SELECT @uids;", header=False)[0][0].decode()

    @get_exceptions
    def get_todays_profit(self):
        """
        Get today's profit perc so far
        Returns float
        """
        command = 'select total_perc from daily_profit LIMIT 1'
        return self.fetch_sql_data(command, header=False)[0][0]

    def get_active_trades(self):
        """
        Get current active trades and store in active_trades table with current price
        """

        self.__run_sql_query("delete from open_trades")
        trades = self.fetch_sql_data("select pair, open_time, open_price, name, `interval`, "
                                     "open_usd_rate*quote_in as usd_quantity from "
                                     "trades where close_price is NULL or close_price=''",
                                     header=False)
        for trade in trades:
            try:
                pair, open_time, open_price, name, interval, usd_quantity = trade
                current_price = get_current_price(pair)
                perc = 100 * (float(current_price) - float(open_price)) / float(open_price)
                perc = - perc if 'short' in name else perc
                insert = ('insert into open_trades (pair, open_time, open_price, current_price, '
                          'perc, name, `interval`, usd_quantity) VALUES ("{0}", "{1}", "{2}", '
                          '"{3}", "{4}", "{5}", "{6}", "{7}")'.format(pair, open_time, open_price,
                                                                      current_price, perc, name,
                                                                      interval,
                                                                      format_usd(usd_quantity)))

                self.__run_sql_query(insert)
            except ZeroDivisionError:
                self.logger.critical("%s has a zero buy price, unable to calculate percentage"
                                     % pair)

    @get_exceptions
    def get_last_hour_profit(self):
        """
        Get profit for the last completed hour
        """
        hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
        date = hour_ago.strftime("%Y-%m-%d")
        hour = hour_ago.strftime("%H")

        command = ('select COALESCE(total_perc,0) total_perc, COALESCE(avg_perc,0) avg_perc, '
                   'COALESCE(usd_profit,0) usd_profit, hour, count(0) from hourly_profit where '
                   'date="{0}" and hour="{1}"'.format(date, hour))

        result = self.fetch_sql_data(command, header=False)
        output = list(result[0])
        output = output[:3]
        output.append(hour)
        return output  # returns total_perc, avg_perc, usd_profit + hour in list

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
                    self.logger.info(" ".join(["Unable to find coin:", coin,
                                               exchange, "KEYERROR"]))
                    continue
                except IndexError:
                    self.logger.critical("Index error %s" % exchange)
                    raise

                try:
                    self.__run_sql_query(command)
                except NameError:
                    self.logger.error("One or more expected variables not passed to insert into DB")
