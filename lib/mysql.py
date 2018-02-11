#!/usr/bin/env python
#pylint: disable=wrong-import-position,import-error,undefined-variable,unused-argument

"""
Push/Pull crypto signals and data to mysql
"""

import os
import sys
import MySQLdb

BASE_DIR = os.getcwd().split('greencandle', 1)[0] + 'greencandle'
sys.path.append(BASE_DIR)

from lib.config import get_config

HOST = get_config('database')['host']
USER = get_config('database')['user']
PASSWORD = get_config('database')['password']
DB = get_config('database')['db']

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
