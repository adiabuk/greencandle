import sys
import pandas as pd
from greencandle.lib import config
config.create_config()
from greencandle.lib.redis_conn import Redis

redis = Redis()
redis.clear_all()
pair='BTCUSDT'
data = {'closeTime':  [1], 'open': [100], 'high': [200], 'low': [300], 'close': [100] }
candle = pd.DataFrame(data, columns = ['closeTime', 'open', 'high', 'low', 'close']).iloc[-1]
print(type(candle))
print(float(candle.close))
redis.update_drawdown(pair, candle, 'open')
print(redis.get_drawdown(pair))  # 0
data = {'closeTime':  [2], 'open': [3], 'high': [4], 'low': [10], 'close': [10] }
candle = pd.DataFrame(data, columns = ['closeTime', 'open', 'high', 'low', 'close']).iloc[-1]
redis.update_drawdown(pair, candle)
print(redis.get_drawdown(pair))  # -90
data = {'closeTime':  [3], 'open': [100], 'high': [200], 'low': [300], 'close': [100] }
candle = pd.DataFrame(data, columns = ['closeTime', 'open', 'high', 'low', 'close']).iloc[-1]
redis.update_drawdown(pair, candle)
print(redis.get_drawdown(pair))  # -90
data = {'closeTime':  [4], 'open': [200], 'high': [300], 'low': [500], 'close': [200] }
candle = pd.DataFrame(data, columns = ['closeTime', 'open', 'high', 'low', 'close']).iloc[-1]
redis.update_drawdown(pair, candle)
print(redis.get_drawdown(pair))  # -90
data = {'closeTime':  [5], 'open': [200], 'high': [300], 'low': [5], 'close': [2] }
candle = pd.DataFrame(data, columns = ['closeTime', 'open', 'high', 'low', 'close']).iloc[-1]
redis.update_drawdown(pair, candle)
print(redis.get_drawdown(pair))  # -95
redis.rm_drawdown(pair)
print(redis.get_drawdown(pair))  # -0
data = {'closeTime':  [6], 'open': [200], 'high': [300], 'low': [5], 'close': [2] }
candle = pd.DataFrame(data, columns = ['closeTime', 'open', 'high', 'low', 'close']).iloc[-1]
redis.update_drawdown(pair, candle)
print(redis.get_drawdown(pair))  # -0

