# Database tables and views

## balance
Table updated frequently by cron and when open order performed
Truncated daily when balance summary is created

## balance_summary
Updated daily by cron for generating OHLC graphs
* ctime - *date - derived from ctime from balance table - time removed*
* usd - *usd fields from balance where COIN is TOTALS*

## daily_profit
View based on profit view - shows average profit by day
* date - *from profit view, time removed*
* perc - *sum of all trade percs grouped by date*

## exchange
static table containing available exchanges
* id - *unique id*
* name - *name of exchange*

## hour_balance
Currently unused

## monthly_profit
View based on profit view - shows average profit by month
* date - *derived from closed_time from profit view - contains only year and month*
* interval - *interval of trade*
* profit -* soon to be deprecated*
* perc - *sum of all trade percs grouped by month/year*

## open_trades
table Updated frequently from cron, shows current status of each open trade
* pair - *pair of current trade*
* open_price - *from trades table*
* open_time - *from trades table*
* current_price - *updated from exchange*
* perc - *calculated from current_price and open_price*
* interval - *from trades table*
* name - *from trades table*

## profit
View based on trades with calculated perc

* open_time - *from trades table*
* interval - *from trades table*
* close_time - *from trades table*
* pair - *from trades table*
* name - *from trades table*
* open_price - *from trades table*
* close_price - *from trades table*
* perc - *calulated from trades table (base in/base out) depending on direction (margin)*
* base_profit - *from trades table from trades table (base in/base out) depending on direction (margin)*
* drawdown_perc - *from trades table*
* drawup_perc - *from trades table*


## profitable
View based on profit table - shows number of winning/lossing trades per trading pair
* pair - *Unique trading pair from profit view*
* total - *Total number of trades for given pair*
* profit - *Number of profitable trades for given pair (perc > 0)*
* loss - *Number of losing trades for given pair (perc < 0)*
* perc_profitable - *percentage of trades which are profitable*

## trades
Main trading table
Entry inserted on each trade open and update on each trade close
* open_time - *time trade was opened*
* close_time - *time trade was closed*
* pair - *trading pair*
* interval - *interval for current trade*
* open_price - *price at trade open*
* close_price - *price at trade close*
* base_in - *base amount used to open trade*
* base_out - *base amount used to close trade*
* quote_in - *quote amount used to open trade*
* quote_out - *quote amount used to close trade*
* name - *strategy nae used to open trade*
* borrowed - *amount of equity borrowed (if margin)*
* multiplier - *multiplier used (if margin)*
* closed_by - *name of strategy used to close trade*
* drawdown_perc - *drawdown perc at end of trade*
* direction - *trade direction: short|long*
* drawup_perc - *drawup perc at end of trade*
