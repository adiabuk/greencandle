#pylint: disable=wrong-import-position,broad-except,no-member,logging-not-lazy,too-many-arguments

"""
Push/Pull crypto signals and data to mysql
"""
import datetime
import MySQLdb
from binance.binance import Binance
from greencandle.lib import config
from greencandle.lib.binance_common import get_current_price
from greencandle.lib.common import AttributeDict, format_usd
from greencandle.lib.logger import get_logger, exception_catcher
from str2bool import str2bool

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
        self.logger.debug("Starting Mysql with interval %s, test=%s" % (interval, test))

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
        self.logger.debug("Running Mysql command: %s" % command)
        try:
            cur.execute(command)
        except MySQLdb.ProgrammingError:
            self.logger.critical("Error running SQL command %s" % command)
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

        self.run_sql_statement('delete from {}'.format(table_name))

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
                     borrowed_usd=0, divisor='0', direction='', symbol_name=None,
                     commission=None, order_id=0):
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
                     quote_in, name, borrowed, borrowed_usd, divisor, direction, open_usd_rate,
                     open_gbp_rate, comm_open, open_order_id) VALUES ("{0}", "{1}", "{2}", "{3}",
                     "{4}", "{5}", "{6}", "{7}", "{8}", "{9}", "{10}", "{11}", "{12}", "{13}",
                     "{14}")
                   """.format(pair, date, '%.15f' % float(price), '%.15f' % float(base_amount),
                              self.interval, quote_amount, config.main.name, borrowed,
                              borrowed_usd, divisor, direction, usd_rate, gbp_rate,
                              commission, order_id)

        result = self.__run_sql_query(command, get_id=True)

        return result

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
                   '> "{3}" and direction="{4}"'.format(pair, date, months, max_perc,
                                                        config.main.trade_direction))

        cur = self.dbase.cursor()
        self.__execute(cur, command)
        return bool(cur.fetchall())

    @get_exceptions
    def get_complete_commission(self):
        """
        Get commission value for open and close trade
        """
        command = ('select commission()')

        cur = self.dbase.cursor()
        self.__execute(cur, command)

        row = [item[0] for item in cur.fetchall()]
        return float(row[0]) if row else None # There should only be one row, so return first item

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
    def get_var_value(self, name):
        """
        get variable from db
        """
        query = "select get_var('{}')".format(name)
        result = self.fetch_sql_data(query, header=False)[0][0]
        return result

    @get_exceptions
    def get_trade_value(self, pair):
        """
        Return details for calculating value of an open trade for a given trading pair
        """

        command = ('select open_price, quote_in, open_time, base_in, borrowed, borrowed_usd '
                   'from trades where close_price is NULL and '
                   '`interval` = "{0}" and pair = "{1}" and name ="{2}" '
                   'and direction="{3}"'.format(self.interval, pair, config.main.name,
                                                config.main.trade_direction))
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
        command = ('select close_time, open_price, close_price, quote_in from trades where '
                   '`interval` = "{0}" and close_price is NOT NULL'.format(self.interval))

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
        command = ('select pair, open_time from trades where close_price is NULL and '
                   '`interval`="{0}" and name in ("{1}","api") and direction like "%{2}%"'
                   .format(self.interval, config.main.name, direction))

        self.__execute(cur, command)
        return cur.fetchall()

    def get_rates(self, quote):
        """
        Get current rates
        return tupple of usd_rate and gbp_rate
        """
        if self.test:
            return (1, 1)
        client = Binance(debug=str2bool(config.accounts.account_debug))
        usd_rate = client.prices()[quote + 'USDT'] if quote != 'USDT' else 1
        gbp_rate = float(usd_rate)/float(client.prices()['GBPUSDT'])
        return (usd_rate, gbp_rate)

    @get_exceptions
    def update_trades(self, pair, close_time, close_price, quote, base_out,
                      name=None, drawdown=0, drawup=0, symbol_name=None, commission=None,
                      order_id=0):
        """
        Update an existing trade with close price
        """
        usd_rate, gbp_rate = self.get_rates(symbol_name)
        job_name = name if name else config.main.name
        query = """select id from trades where close_price is NULL and `interval`="{0}"
                   and pair="{1}" and (name="{2}" or name like "api") and direction="{3}"
                   ORDER BY ID ASC LIMIT 1
                """.format(self.interval, pair, job_name, config.main.trade_direction)
        try:
            trade_id = self.fetch_sql_data(query, header=False)[0][0]
        except IndexError:
            self.logger.critical("No open trade matching criteria to close: %s" % query)
            return None

        command = """update trades set close_price={0},close_time="{1}",
        quote_out="{2}", base_out="{3}", closed_by="{4}", drawdown_perc=abs(round({5},1)),
        drawup_perc=abs(round({6},1)), close_usd_rate="{7}", close_gbp_rate="{8}",
        comm_close="{9}", close_order_id="{10}" where id = "{11}"
        """.format('%.15f' % float(close_price), close_time, quote,
                   '%.15f' % float(base_out), job_name,
                   drawdown, drawup, usd_rate, gbp_rate, str(commission), order_id, trade_id)

        self.__run_sql_query(command)

        return trade_id

    @get_exceptions
    def get_todays_profit(self):
        """
        Get today's profit perc so far
        Returns float
        """
        command = ('select usd_profit, usd_net_profit, avg_perc, avg_net_perc, total_perc, '
                   'total_net_perc, count from profit_daily where date(date) = date(NOW())')

        row = self.fetch_sql_data(command, header=False)
        return row[0] if row else [None] * 7

    def get_active_trades(self):
        """
        Get current active trades and store in active_trades table with current price
        """

        client = Binance(debug=str2bool(config.accounts.account_debug))
        prices = client.prices()
        self.__run_sql_query("delete from open_trades")
        trades = self.fetch_sql_data("select pair, open_time, open_price, name, `interval`, "
                                     "open_usd_rate*quote_in as usd_quantity, direction from "
                                     "trades where close_price is NULL or close_price=''",
                                     header=False)
        for trade in trades:
            try:
                pair, open_time, open_price, name, interval, usd_quantity, direction = trade
                current_price = get_current_price(pair, prices)
                perc = 100 * (float(current_price) - float(open_price)) / float(open_price)
                perc = - perc if 'short' in direction else perc
                net_perc = perc - float(self.get_complete_commission())
                insert = ('replace into open_trades (pair, open_time, open_price, current_price, '
                          'perc, net_perc, name, `interval`, usd_quantity, direction) VALUES '
                          '(" {0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}", "{7}", "{8}", "{9}")'
                          .format(pair, open_time, open_price, current_price,
                                  perc, net_perc, name, interval,
                                  format_usd(usd_quantity), direction))

                self.__run_sql_query(insert)
            except ZeroDivisionError:
                self.logger.critical("%s has a zero open price, unable to calculate percentage"
                                     % pair)

    def trade_in_context(self, pair, name, direction):
        """
        Check if a trade exists for given pair, name, and direction
        """

        query = ("select * from open_trades where pair={0} and name={1} and direction={2}"
                 .format(pair, name, direction))
        result = self.fetch_sql_data(query, header=False)
        return book(result)



    @get_exceptions
    def get_last_hour_profit(self, date=None, hour=None):
        """
        Get profit for the last completed hour
        """
        hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
        date = date if date else hour_ago.strftime("%Y-%m-%d")
        hour = hour if hour else hour_ago.strftime("%H")

        command = ('select COALESCE(total_perc,0) total_perc, '
                   'COALESCE(total_net_perc,0) total_net_perc, '
                   'COALESCE(avg_perc,0) avg_perc, '
                   'COALESCE(avg_net_perc,0) avg_net_perc, '
                   'COALESCE(usd_profit,0) usd_profit, '
                   'COALESCE(usd_net_profit,0) usd_net_profit, '
                   'COALESCE(num_trades,0) num_trades '
                   'from profit_hourly where '
                   'date="{0}" and hour="{1}"'.format(date, hour))
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
        command = ('select pair, borrowed, direction from trades '
                   'where pair like "%{0}%" and name like "%{1}%" '
                   'and close_price is NULL'.format(pair, account))

        cur = self.dbase.cursor()
        self.__execute(cur, command)

        rows = cur.fetchall()
        return rows if rows else ()

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
