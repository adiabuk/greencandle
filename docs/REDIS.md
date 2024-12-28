# Redis

# Keys:
Main keys are categorized by pair and interval in the following format:
  {pair}:{interval}
  eg. "XRPBTC:1h", "BTCUSDT:5m" etc.

  This contains a hash.  The top level keys are the milli-epoch
  eg "1664482499999", "1664480399999"
  Each of these epochs contain the data for the epoch.  The keys at this level are the indicator
  names as well as the candle data and current price (close)
  eg. EMA_200, EMA_50 RSI_14, middle_20, ohlc
  An additional key of current_price is also added, containing the close_price (also within ohlc)

  The ohlc data is pickled and then compressed with zlib

  At this level  each key contains the data as the value with no additional levels


##  Main methods
* redis_conn
Add data to redis
Takes ohlc and indicator data from engine module and send it to redis

* get_intervals
Get list of sorted keys (mepoch) for a given pair/interval
* get_item
Get an item using pair, interval and item (mepoch)
* get_current
get ohlc data or current price from redis for a given pair/interval and item (mepoch)
* get_result
get result of a particular indicator for a given pair/interval item (mepoch) and indicator


## Helper scripts

* cleanup_redis
Clear old items (mepoch) from redis based on age
* clear_redis
delete all redis data


## Log warnings
TBD

## Debugging
TBD
