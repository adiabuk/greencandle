#!/usr/bin/env python
#pylint: disable=wrong-import-position,import-error

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

def insert_data(interval, symbol, event, direction, data, difference, resistance, support):
    """
    id, symbol, time, event, direction, data
    """

    db = MySQLdb.connect(host=HOST,
                         user=USER,
                         passwd=PASSWORD,
                         db=DB)


    cur = db.cursor()
    command = """INSERT INTO data (symbol, event, direction, data, difference, resistance, support)
    VALUES ("{0}","{1}","{2}","{3}","{4}","{5}","{6}");""".format(symbol, event, direction, data, difference, resistance, support)

    cur.execute(command)

    db.commit()

def insert_alert(**kwargs):
    """
    date, symbol, event, direction, direction, hold, data_id
    """
    pass
