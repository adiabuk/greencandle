#!/usr/bin/env python

"""
Get results from redis for a paricular run
"""

import ast
import os
import sys

from ..lib import config
config.create_config()
from ..lib.redis_conn import Redis

def get_all_details(address):
    """
    get details for particular address and action
    """
    pair, interval, _ = address.split(":")
    redis = Redis('1m', db=0)
    all_items = [x.decode("utf-8") for x in list(redis.get_items(pair, interval))]
    start_index = all_items.index(address)
    all_items = all_items[start_index:]
    for address in all_items:
        total = redis.get_total(address)
        details = list(redis.get_details(address))
        mepoch = address.split(":")[-1]
        dict_item = ast.literal_eval(details[0][-1].decode())
        price = dict_item['current_price']
        print("{0},{1},{2}".format(mepoch, price, total))

def get_details(address):
    for item in details:
        dict_item = ast.literal_eval(item[-1].decode())
        print(dict_item)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {0} [address]".format(sys.argv[0]))
        sys.exit(2)
    get_all_details(sys.argv[1])
