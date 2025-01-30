"""
objects module
"""
class AttributeDict(dict):
    """Access dictionary keys like attributes"""
    def __init__(self, *args, **kwargs):
        def from_nested_dict(data):
            """ Construct nested AttrDicts from nested dictionaries. """
            if not isinstance(data, dict):
                return data
            return AttributeDict({key: from_nested_dict(data[key])
                                for key in data})

        super().__init__(*args, **kwargs)
        self.__dict__ = self

        for key in self.keys():
            self[key] = from_nested_dict(self[key])

    def __del_attr__(self, attr):
        self.pop(attr, None)

class Bcolours:
    """
    Unicode colors for text hilighting
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
          "12h": 720,
          "1d": 1440,
          "1w": 10080
          }
