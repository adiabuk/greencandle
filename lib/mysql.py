#pylint: disable=wrong-import-position,import-error,undefined-variable,unused-argument

"""
Push/Pull crypto signals and data to mysql
"""

import os
import sys
import MySQLdb
import binance
import MySQLdb.cursors

BASE_DIR = os.getcwd().split('greencandle', 1)[0] + 'greencandle'
sys.path.append(BASE_DIR)

from lib.config import get_config

HOST = get_config('database')['host']
USER = get_config('database')['user']
PASSWORD = get_config('database')['password']
DB = get_config('database')['db']

def get_buy():
    potential_buys = get_changes()

    for x in potential_buys.keys():
        # get count: cursor.execute("SELECT COUNT(*) FROM trades")
        # if count < max: buy, else return
        # order by buy strength - from action_totals
        print(" About to buy {0} at {1}".format(x, potential_buys[x][-1]))


def get_sell():
    #
    pass

def trade():
    pass

def get_changes():
    command = """
    select s1.pair AS pair, s1.ctime AS ctime, ((s1.total <= 0) and (s2.total >= 0)) AS gt from (action_totals s1 left join action_totals s2 on  ((s1.pair = s2.pair))) where   ((s1.total <> s2.total) and  ((s1.total < 0) and (s2.total >0)))  limit 20;
    """
    return fetch_sql_data(command)

def fetch_sql_data(query):
    di = {}
    db = MySQLdb.connect(host=HOST,
                         user=USER,
                         passwd=PASSWORD,
                         db=DB,
                         cursorclass=MySQLdb.cursors.DictCursor)
    prices = binance.prices()
    try:
        with db.cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
            for record in data:
                di[record['pair']] = record['ctime'], prices[record['pair']]

    finally:
        db.close()
    return di

def run_sql_query(query):
    db = MySQLdb.connect(host=HOST,
                         user=USER,
                         passwd=PASSWORD,
                         db=DB)



    cur = db.cursor()
    try:
        cur.execute(query)
    except NameError:
        print("One or more expected variables not passed to DB")

    db.commit()

def clean_stale():
    command1 = "delete from action_totals where ctime < NOW() - INTERVAL 15 MINUTE;"
    command2 = "delete from actions where ctime < NOW() - INTERVAL 15 MINUTE;"
    run_sql_query(command1)
    run_sql_query(command2)

def insert_data(**kwargs):
    """
    id, symbol, time, event, direction, data
    """
    globals().update(kwargs)
    db_instance = MySQLdb.connect(host=HOST,
                                  user=USER,
                                  passwd=PASSWORD,
                                  db=DB)

    cur = db_instance.cursor()
    command = """INSERT INTO data (symbol, event, direction, data, difference, resistance, support,
    buy, sell, market, balance)
    VALUES ("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}");""".format(
        symbol, event, direction, data, difference, resistance, support, buy, sell, market, balance)
    try:
        cur.execute(command)
    except NameError:
        print("One or more expected variables not passed to insert into DB")

    db_instance.commit()


def insert_balance(d):

    db_instance = MySQLdb.connect(host=HOST,
                                  user=USER,
                                  passwd=PASSWORD,
                                  db=DB)

    cur = db_instance.cursor()
    for exchange, values in d.items():
        for coin, data in values.items():
            try:
                command = """insert into balance (gbp, btc, usd, count, coin, exchange_id) values
                ("{0}", "{1}", "{2}", "{3}", "{4}", (select id from exchange where
                name="{5}"))""".format(data['GBP'], data['BTC'], data['USD'], data['count'], coin,
                exchange)
            except KeyError:
                print("XXX", coin, exchange, "KEYERROR")
                continue
            except IndexError:
                print(exchange)
                raise

            try:
                cur.execute(command)
            except NameError:
                print("One or more expected variables not passed to insert into DB")

    db_instance.commit()



def insert_alert(**kwargs):
    """
    date, symbol, event, direction, direction, hold, data_id
    """
    pass

def insert_action_totals():
    command = """ INSERT INTO action_totals (pair, total) select pair, SUM(action) as total from
    recent_actions group by pair order by total;"""
    run_sql_query(command)

def insert_actions(**kwargs):
    globals().update(kwargs)

    command = """INSERT INTO actions (pair, indicator, value, action)
                 VALUES ("{0}","{1}","{2}","{3}");""".format(pair, indicator, value, action)

    run_sql_query(command)
