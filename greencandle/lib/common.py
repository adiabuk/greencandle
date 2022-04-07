"""
Common functions that don't belong anywhere else
"""

from decimal import Decimal
import numpy

MINUTE = {"3m": "0,3,6,9,12,15,18,21,24,27,30,33,36,39,42,45,48,51,54,57",
          "5m": "0,5,10,15,20,25,30,35,40,45,50,55",
          "15m": "0,15,30,45",
          "30m": "0,30",
          "1h": "0",
          "2h": "0",
          "3h": "0",
          "4h": "0",
          }

HOUR = {"3m": "*",
        "5m": "*",
        "15m": "*",
        "30m": "*",
        "1h": "*",
        "2h": "0,2,4,6,8,10,12,14,16,18,20,22",
        "3h": "0,3,6,9,12,15,18,21",
        "4h": "0,4,8,12,16,20"
        }

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
        pip_value = int((str(value) + "000").split(".")[-1][:4])
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
    return float(num) * (1 - float(perc)/100)

def perc_diff(num1, num2):
    """
    Get percentage difference between 2 numbers
    """
    return ((float(num2) - float(num1))/ abs(float(num1))) * 100

def convert_to_seconds(string):
    """conver human readable duration to seconds"""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    return int(string[:-1]) * seconds_per_unit[string[-1]]
