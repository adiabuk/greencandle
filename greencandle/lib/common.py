#pylint: disable=no-member
"""
Common functions that don't belong anywhere else
"""

import os
import sys
import datetime
from decimal import Decimal, InvalidOperation
import yaml
from babel.numbers import format_currency
import numpy
from markupsafe import Markup

QUOTES = ("BTC", "USDT", "ETH", "BNB", "GBP")

MINUTE = {"1m": "*",
          "3m": "*",
          "5m": "*",
          "15m": "0,5,10,15,20,25,30,35,40,45,50,55",
          "30m": "0,10,20,30,40,50",
          "1h": "01",
          "2h": "0,10,20,30,40,50",
          "3h": "0,10,20,30,40,50",
          "4h": "0,30",
          "12h": "0",
          "1d": "0",
          }

HOUR = {"1m": "*",
        "3m": "*",
        "5m": "*",
        "15m": "*",
        "30m": "*",
        "1h": "*",
        "2h": "*",
        "3h": "*",
        "4h": "*",
        "12h": "*",
        "1d": "*"
        }

TF2MIN = {"1s": 1,
          "1m": 1,
          "3m": 3,
          "5m": 5,
          "15m": 15,
          "30m": 30,
          "1h": 60,
          "2h": 120,
          "3h": 180,
          "4h": 240,
          "12h": 720
          }

def get_short_name(name, env, direction):
    """
    Get short name for a container
    """
    if direction not in name:
        name = f"{name}-{direction}"
    try:
        short = list_to_dict(get_be_services(env), reverse=False)[name]
    except KeyError:
        short = "xx"
    return short

def get_be_services(env):
    """
    Get long/short services from docker-compose file
    """

    with open(f"/srv/greencandle/install/docker-compose_{env}.yml", "r") as stream:
        try:
            output = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    links_list = output['services'][f'{env}-be-api-router']['links']
    return links_list

def get_worker_containers(env):
    """
    Get list of worker containers in given environments
    """
    containers = []
    with open(f'/srv/greencandle/install/docker-compose_{env}.yml', 'r') as stream:
        output = yaml.safe_load(stream)
        keys = list(output['services'].keys())
        for key in keys:
            if 'be-api-' in key or 'be-eng-' in key:
                containers.append(key)

    return containers

def list_to_dict(rlist, reverse=True, delimiter=":", str_filter=''):
    """
    Convert colon seperated string list to key/value dict
    """
    links = dict(map(lambda s: s.split(delimiter), rlist))
    if reverse:
        return {v: k for k, v in links.items() if str_filter in k}
    return {k: v for k, v in links.items() if str_filter in k}

def divide_chunks(lst, num):
    """
    Divide list into lists of lists
    using given chunk size
    """

    # looping till length l
    for i in range(0, len(lst), num):
        yield lst[i:i + num]

def format_usd(amount):
    """
    Return formatted USD string, with dollar sign and 2dp
    """
    try:
        return str(format_currency(amount, 'USD', locale='en_US'))
    except InvalidOperation:
        return "N/A"

def arg_decorator(func):
    """
    Add --help arg to simple scripts with text from function docstring
    """
    def inner(*args, **kwargs):
        if len(sys.argv) > 1 and sys.argv[1] == '--help':
            print(func.__doc__)
            sys.exit(0)
        return func(*args, **kwargs)
    return inner

class AttributeDict(dict):
    """Access dictionary keys like attributes"""
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value
    def __del_attr__(self, attr):
        #del self[attr]
        self.pop(attr, None)

def percent(perc, num):
    """return percentage of a given number"""
    return (num * perc) /100

def make_float(arr):
    """Convert dataframe array into float array"""
    return numpy.array([float(x) for x in arr.values], dtype='f8')

def pip_calc(open_val, close_val):
    """Get number of pips between open and close"""
    open_val = Decimal(open_val)
    close_val = Decimal(close_val)
    if "." not in str(open_val):
        multiplier = Decimal(0.0001)
    elif str(open_val).index(".") >= 3:  # JPY pair
        multiplier = Decimal(0.01)
    else:
        multiplier = Decimal(0.0001)

    pips = round((close_val - open_val) / multiplier)
    return int(pips)

def pipify(value):
    """
    return 4 digits after decimal point
    representing the pip
    as an int
    """
    value = Decimal(value)
    try:
        pip_value = int((str(value) + "000").rsplit(".", maxsplit=1)[-1][:4])
        return pip_value
    except ValueError:
        print("Value Error", value)
        return None

def add_perc(perc, num):
    """
    Add a percentage to a number
    Args:
        perc: Percent num to add
        num: number to add to
    Returns:
        total: num + perc%
    """

    return float(num) * (1 + float(perc)/100)

def sub_perc(perc, num):
    """
    Subtractsa percentage to a number
    Args:
        perc: Percent num to subtract
        num: number to subtract from
    Returns:
        total: num - perc%
    """
    perc = -(perc) if float(num) < 0 else perc
    return float(num) * (1 - float(perc)/100)

def perc_diff(num1, num2):
    """
    Get percentage difference between 2 numbers
    """
    return ((float(num2) - float(num1))/ abs(float(num1))) * 100

def convert_to_seconds(string):
    """conver human readable duration to seconds"""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800,
                        "M": 2628288, "Y": 31536000}
    return int(string[:-1]) * seconds_per_unit[string[-1]]

def epoch2date(epoch, use_spaces=True, formatted=True):
    """
    Convert epoch to human readable formatted string
    """
    format_str = '%Y-%m-%d %H:%M:%S' if use_spaces else '%Y-%m-%d_%H-%M-%S'
    time_stamp = datetime.datetime.fromtimestamp(epoch)
    return time_stamp.strftime(format_str) if formatted else time_stamp

def get_tv_link(pair, interval=None, anchor=False):
    """
    Return Tradingview hyperlink for slack notifications
    """

    minutes_per_unit = {"s":1, "m": 1, "h": 60, "d": 1400, "w": 10080}
    def convert_to_minutes(time_string):
        return int(time_string[:-1]) * minutes_per_unit[time_string[-1]]

    if anchor:
        return Markup(f'<a href="https://www.tradingview.com/chart/?symbol=BINANCE:{pair.strip()}'
                      f'&interval={convert_to_minutes(interval)}" target="_blank">{pair}</a>')

    if interval:
        return (f"<https://www.tradingview.com/chart/?symbol=BINANCE:{pair.strip()}"
                f"&interval={convert_to_minutes(interval)}|{pair.strip()}>")
    return f"<https://www.tradingview.com/chart/?symbol=BINANCE:{pair.strip()}|{pair.strip()}>"

def get_trade_link(pair, strategy, action, string, port=8888, anchor=False, short=False):
    """Get trade link for forced trade"""
    url = "" if short else "http://" + os.environ['VPN_IP'] + ":" + port
    if anchor:
        return Markup(f'<a href="{url}/action?pair={pair.strip()}&strategy='
                      f'{strategy.strip()}&action={action.strip()}&close=true" target="_blank">'
                      f'{string.strip()}</a>')

    return (f"<{url}/action?pair={pair.strip()}&strategy={strategy.strip()}"
            f"&action={action.strip()}&close=true|{string.strip()}>")
