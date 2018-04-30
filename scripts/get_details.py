#!/usr/bin/env python

"""
Get results from redit for a paricular run
"""

import ast
import os
import sys

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)
from lib.redis_conn import Redis

def get_details(address, action):
    """
    get detaild for particular address and action
    """
    redis = Redis('5m', db=0)
    details = list(redis.get_details(address))  # KNCBTC BUY
    for item in details:
        dict_item = ast.literal_eval(item[-1].decode())
        if dict_item['action'] == action:
            print(item[0], dict_item['action'])

if __name__ == "__main__":
    get_details(sys.argv[1], sys.argv[2])
