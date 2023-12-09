
# Orders

## Items list
items_list - passed to order.Trade.open_trade | order.Trade.close_trade
list of tuples containing the following:

* item: *(pair: string) eg BTCUSDT*
* current_time: *YYYY-MM-DD h:m:s eg 2021-01-24 01:14:59*
* current_price: *current price of trading pair*
* event: *type of buy/sell from redis.Redis.get_action/get_intermittent eg StopLoss*
* action: str  1 for long, -1 for short
* max_usd: int max usd to use for given trade

# Type of order

Determined in code by parsing config

open_order: order.Trade.open_trade()
close_order: order.Trade.close_trade()

long/short and spot/margin determined from the following config options
* config.main.trade_direction: *long|short*
* config.main.trade_type: *spot|margin*


