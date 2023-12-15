# Main configuration: greencandle.ini

## [email]  *Email notifications section*
* **email_from** *email from - gmail login*
* **email_to** *email to*
* **email_password** *gmail password*
* **email_active** *{True|False} email notifications active*

## [slack]  *Slack notifications section*
* **slack_active** *{True|False} Slack notifications active*
* **alerts** *Name of alerts channel for current env*
* **trades** *Name of trade channel for current env*
* **balance** *Name of balance channel for current env*
* **notifications** *Name of notifications channel for current env*
* **url** *Webhook url for all notifications*


## [database]  *Mysql database*
* **db_host** *mysql hostname/ip*
* **db_user** *mysql username*
* **db_password** *mysql password*
* **db_database** *mysql database name*

## [redis]  *Redis keystore database*
* **redis_host** *redis hostname/IP*
* **redis_port** *redis port*
* **redis_expiry_seconds** *Redis key expiry seconds - active if > 0*

##[pairs]  *Pairs for all strategies in current environment - used by FE containers*

## [accounts]  *Exchange details*
* **account{1-4}\_type** *{Phemex|Coinbase|Binance}
* **account{1-4}\_key** *exchange key*
* **account{1-4}\_secret** *exchnage secret*

## [main] *Main config section for trade details*
* **name** *Name of container*
* **trade_type** *{spot|margin}*
* **trade_direction** *long|short*
* **multiplier** *leverage for margin*
* **production** *True|False whether or not to run binance methods*
* **logging_level** *0(NOSET)|10(DEBUG)|20(INFO)|30(WARNING)|40(ERROR)|(50(CRITICAL)*
* **logging_output** *stdout|journald*
* **max_trades** *max number of trades per container*
* **divisor** *divide available funds by this figure*
* **interval** *1m|3m|5m|15m|30m|1h|4h|1d*
* **wait_between_trades** *True|False*
* **time_between_trades** *{1m|30h|1w} time between close and open*
* **time_in_trade** *{1m|30h|1w} time before auto-closing trade*
* **perc_at_timeout** percentage to wait for once timeout has been reached
* **immediate_stop** *{True|False} Stop immediately after stop loss reached or wait for candle close*
* **immediate_trailing_stop** *{True|False} Stop immediately after stop trailing stop loss reached or wait for candle close*
* **immediate_take_profit** *{True|False} Stop immediately after take profit reached or wait for candle close*
  **trailing_start** *percentage to commence trailing stop loss check*
* **drain** *Only close trades, don't open new ones*
* **no_of_klines** *number of candles to download initially*
* **pairs** *list of trading pairs*
* **stop_loss_perc** *stop loss percentage*
* **take_profit_perc** *Take profit percentage - disabled if 0 or less*
* **trailing_stop_loss_perc** *Trailing stop loss percentage from maximum value since open - disabled if 0 or less*
* **indicators** *List of indicators and values - see seperate doc*
* **open_rule{1-3}** *Rules to open trade - see seperate doc*
* **close_rule{1-3}** *Rules to close trade - see seperate doc*
* **rate_indicator** *indicator to use for tracking slope increase/decrease*
