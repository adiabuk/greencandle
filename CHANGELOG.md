
# Releases

# 3.6
* Fix for lower timeframe timestamps being truncated
* Consolidate router configs into a single template
* Remove backups from gc cron
* Get owed borrowed amount from exchange before repaying
* Deduct commission from amount held on trade-open
* Log commission data to DB
* Fix for incompatibility issue between mysql version and dump tool
* Add default value for borrowed amount/multiplier for all trades
* Check for borrowed amount before attempting to repay it
* Fix profit amount for short trades
* Show profit/perc net of commission in notifications

# 3.5
* Alert redirection from all envs
* add Supertrend and StochRSI indicators
* Add environment name to audio alert
* Have variable SL/TP based on entry conditions
* Remove old 5ma/env istrategy environments
* Allow code to decide to go long/short basied on float action
* Log all api requests to local db of given environment
* Add all router assocs from personal env into prod env
* Minor bugfixes
* Lint & layout fixes

## 3.4.1
* Deployment and image bugfixes

## 3.4
* Transition to homegrown Jenkins and deprecate Travis CI
* Reinstate audio and visual alerts
* Link alerts to per and prod environments
* Improve data env strategies
* Splitting of large unit tests for concurrency
* Stop debug logs on data env
* Better test logging
* Add static libraries to base images to reduce deploy/test time
* Add container name to exception alert
* Add logwatch to data env
* Fix monthly profit db view
* Add weekly profit db view
* Add more visibility of environments in UI to avoid confusion
* Rewrite URL after open/close trade to avoid dupe command sent to api

## 3.3
* Try to increase next trade in same strategy
* Cleanup drawdown/drawup tools into single script
* Catch balance exception when cross account not available
* Show when next iteration of analysis begins is slack
* add API key for staging for API and light alert
* Use max_borrow from binance for balances
* Show list of supported trades in analysis alerts

## 3.2
* Speed up & scale data analysis
* Fixes for BNB cross account debts
* Allow converting to/from GBP as trade asset

## 3.1
* Fixes and tests for Api Router links/assocs
* Fix USD profit in DB for short trades
* Display BNB debt in balance notification
* Reformatting of slack notifications
* Use docker volume to wait for fresh data to analyse
* Still update the DB when we fail to repay loan
* Borrow full amount for short trades but only use 99%

## 3.0.2
* Typos and bug fixes

## 3.0.1
* docker compose bug fixes
* move releases to changelog file

## 3.0
* Short methods implemented
* Short API strategies for prod/per/stag/data envs
* New channel for trade alerts
* Better layout/formatting for slack notifications
* Code consolidation
* Reduce travis build time
* Cleanup of empty balance alerts

## 2.21.1
* New api keys
* Unit test fixes
* Security fixes

## 2.21
* Tradingview links for slack notifications
* Cleanup slack notifications - don't send when there is no data
* Don't use Phemex in all environments
* Cleanup unused code and libs
* Standardize consolidate code and static vars into common module
* Speed up unit tests by abstracting into base image and removing repeated code
* Cleanup de-listed trading pairs
* Add data analyser in separate environment

## 2.20.1
* Speed up balance iteration by removing zero balance entries before loop
* Remove various delisted pairs
* Add data env to staging
* Name fixes for data env
* Fix staging alert container
* Add logwatch to prod
* Fix binance for currency conversion
* Analyse data more frequently for collection overlap
* Add trade alert to log as well as slack notifications

## 2.20
* Trade alert containers for data collection and analysis
* logwatch container for alerting on exceptions
* Send quote amounts to slack
* Cleanup of unit tests
* Tests for checking all environment config and failing with empty values
* More logging for trade and trade/loan failures
* Better checking of available funds to close trade (inc commission)
* Check if sufficient BNB available for each trade close
* Check for big recent price drops and alert
* Switch currency conversion to use binance

## 2.19.2
* Log return dict from exchange after open/close trade
* Fix critical spot balance bug

## 2.19.1
* Small type and name fixes

## 2.19
* Use latest version of binance to allow testing API
* Fix cross margin close trade

## 2.18
* Working prod api keys
* Test env with buy alerts
* Save time during testing by not building images twice
* Code cleanup/consolidation

## 2.17.2
* Small syntax fixes

## 2.17.1
* APi container name fixes
* fix assocs for staging
* Assocs unit testing
* Fix title in WebUI and Slack alerts
* C9e base dir fix
* Reduce frequency of test_close cron run
* Seperate out spot/cross/isolated in API dashboard

## 2.17
* Fix loan calculations for cross margin
* Fix amount for NOT USDT margin pairs
* Add env name to logging
* Ensure all slack alerts contain env name
* Log to slack when too many open trades for a given container

## 2.16.2
* Small var name fix

## 2.16.1
* Fixes to 9e keys
* Correlate new env names acroos platorm
* Removal of old api keys
* Fix for SSL timeout during unit tests

## 2.16
* Fixes to bootstrap scripts
* Fixes to SQL templates
* Add per environment to prod deployment
* Switch prod/per
* Increase vagrant specs
* Fixes to RSI indicator and graph
* Cleanup of old envs
* Allow trading with GBP quote
* Allow reducing of concurrent data fetching from exchange
* Re-retrieve initial data on each new run

## 2.15
* Allow any assets to be traded from dashboard
* Correct strategy/container names
* Increase redis expiry time
* Store quote amount to isolated balances
* Share bash history with containers
* Add environment to HTML page titles
* Re-enable alert container and reduce volume

## 2.14.1
* Fix invalid environment paths

## 2.14
* Correct quote/base in DB and code
* Additional test strategies in staging
* Database changes will be performed manually during release
* Strategies for trading any pair from dashboard
* Re-enable travis notifications
* Create builds automatically after travis tests have passed
* General cleanup of DB & code


## 2.13
* Fixes to isolated close long trades
* Get correct base amount from exchange
* Rename remaining non-api containers
* Add missing api token in dashboard

## 2.12
* Compare amount with value from exchange when selling
* Create docker builds after travis tests
* Use API token for requests from trading view
* Travis fixes to login to docker again
* Restart docker containers on all failures
* Fix buy/borrow amounts for isolated

## 2.11
* Display profit in USD at end of trade
* More alerting if trade is not made
* Initial API documentation
* Fix link to travis UI

## 2.10.1
* Fix API dashboard
* Fix Memory Leak when selling multiple items
* Re-enable test-run
* Update Travis URL

## 2.10
* Fix broken cross margin trades
* Improve slack error logging
* Use amount bought value from exchange
* Rename /install dir to /srv/greencandle in containers
* Rename scripts dir to bin
* Stag container allowed to trade any pair
* Allow duplicate trades to be closed individually
* Add json checks to tests
* Add USD and GBP exchange rates to each buy/sell order in DB

## 2.9.2
* Bump binance version for correct isolated balances

## 2.9.1
* Add missing pair for container

## 2.9
* Create docker images manually
* Test open trades periodically through cron
* Alert on trade close failure
* Small travis-ci fixes
* Don't reimport config in order module
* Rename spot config and containers
* Increase spot trading volume

## 2.8
* Use new currency conversion module
* Merge env 1m and 15m into single top level config
* Remove pair delisted from binance
* Update virtualbox spec
* Fix healthcheck for APIs
* Add new tests to staging
* Fixes for amount to use/borrow

## 2.7.1
* Fix mising dashbaord link in prod
* Get remaining loan amount and current debt for cross calculations
* Add healthcheck for dashboard
* Adjust cross margin trade multiplier

## 2.7
* New API dashboard for charts and trades
* New database views for stats and insights
* Small database and query fixes
* New isolated containers for 1m BTC and USDT trades
* Remove old api and dashboard
* Reduce deploy time now that most trades are through api
* Fixes due to third party changes to python-forex and ccxt
* Increase logging for margin borrow failures
* Add primary key to trades db table
* Make container name consistent

## 2.6.1
* Additional pairs for 1m env and 3h 5MA strategies
* New containers for new base pairs
* Update docker-compose version
* Auto-pull all images in docker-compose
* Correctly calculate spot margin balance by including debt as negative equity
* Clean alert noice in slack

## 2.6
* Decrease volume of alerts down to 10% during out-of-hours
* Cleanup lint
* Bug fix with multiple concurrent trades
* Allow cross margin trades access to total balance when calculating how much to use
* Remove some pairs from 1m strategy
* Fixes for max trades per strategy
* Added small script for quickly retrieving current price of trading pair
* Suppress meaningless slack alerts

## 2.5
* Rename margin strategies to cross or isolated
* Small fixes to missing containers and trading pairs
* Add alerting endpoint to staging environment
* Fixes to balance graph with isolated balance
* Increase trade margins

## 2.4.3
* New env 1m strategies
* Fix divisor value in config for all pairs
* Additional pairs for all strategies

## 2.4.2
* Fix incorrect config
* Add env 1m strategy to prod
* Fix typo in router config
* Log each deployment to syslog

## 2.4.1
* Cleanup isolated margin balance code
* Use newer version of binance module
* Don't request balance twice when running cron

## 2.4
* Use API for incoming trades
* Port/host mappings for API containers
* Route API traffic to multiple concurrent containers (eg. for margin/alternate exchange)
* Add sport and margin API containers for long trades
* Add new methods for calculating isolated margin balance totals
* Fixes for 5MA strategy SL/TP

## 2.3
* Fix isolated margin balance
* Get correct balance for long isolated margin trades
* 5MA trigger fixes
* Add isolated margin 5MA trades
* Tweak multiplier and divisor values
* Fixes to sell-now script

## 2.2.4
* Fix typo

## 2.2.3
* Show backend test status in command line
* Remove test argument from all prod instances
* Add isolated margin trade to config
* Enable trading with isolated margin pairs
* Fix for 5ma prod to only buy at breakout point

## 2.2.2
* Naming of api backend container
* Fix stag dependencies
* Enable full prod rsi-tsi api strategy
* Cleanup
* Use latest binance module

## 2.2.1
* Fix backend api dependencies in prod
* Fix syntax in graph module

## 2.2
* API for receiving trading notifications
* New trading pairs and strategies based on long-term stag results

## 2.1.1
* Fix DB syntax error

## 2.1
* Allow graph module to be backwards compatible with data in redis
* Create BTC balance graphs as well as USD
* Use 99% of margin borrowed funds
* Add short tests
* Negate perc for short trades in slack
* Increase equity for 5ma prod
* Remove timeInForce arg for margin trades
* Combine trade notifications into single method
* Add strategy name to open trades notifications

## 2.0.2
* Use pairs tested in staging
* Cleanup var names and dupe code
* Lint and consistency fixes
* Get balance only for exchange/account we are trading
* Use quote value for margin quantity

## 2.0.1
* use correct trailing stop var in test
* Ensure drawup/drawdown are wiped on new trade
* Add more logging to idenitfy balance issue
* Ensure we don't attempt to buy more than current balance
* Small change to prod pairs
* Add scalp stop loss
* Add 5ma 1tsl to prod

## 2.0
* Add margin strategies to prod
* Re-enable 5MA strategy in prod
* Add ETH and BNB scalp strategies
* Better trade notifications with symbols
* Better formatting for balance notifications
* More informative alerts for trade failures
* Fixes for trailing stop loss
* Scalp strategy enhancements
* Restart all containers on failure
* Fix logging reporting wrong module
* Remove logs not using logging module
* API enhancements

## 1.9.1
* Remove new release of cryptography causing built issues
* Limit scalp prod to 1 concurrent trade

## 1.9
* Fix prod scalp
* Unit tests for TP/SL/TSL
* Fix for balance graph
* Lint fixes
* Better trade notifications
* Better trade amount calc
* Bug fix, open trades showing overlapping strategies
* Updated docs
* Better profit and daily profit db view

## 1.8
* Enhancements to slack trade alerts
* Cleanup of lint and dupe code
* Fix for drawup calculations
* Added more unittests
* Only 1 trade per strategy in prod
* More tests in stag
* DB Cleanups

## 1.7.1
* Fix broken link for downloading ta-lib
* temporarily disable 5ma in prod

## 1.7
* Remove underperforming prod strategies
* Cleanup TSP and TP config options
* Add OHLC graph for daily balance
* Cleanup lint and dupe code
* Fix missing event in graphs
* Cleanup API debug messages
* Margin long trades ready for testing
* Use higher equity for prod trades

## 1.6.1
* Move 5MA and scalp strategies from stag to prod
* Fix for redis unittests
* Disable prod push notifications
* Disable prod debug messages

## 1.6
* Updated prod scalp strategy
* Additional unit tests
* Code cleanup
* Trailing Stop Loss bug fix
* Temp Api fix for multiple timeframes
* More frequent intermittent price checks
* DB fix for monthly view
* Remove implicit volume from graph
* Config cleanup
* Deploy script enhancements
* Doc update

## 1.5
* Add draw up to db
* fix trailing stop loss
* DB config for drawup
* better default values for TSI oscillator
* Get downloads from dropbox
* Use drawup/drawdown for high/low prices within trade
* Add trailing stop loss to intermittent function
* Add immediate stop option for trailing SL and TP separately
* Unit tests for draw up/down
* New scalp strategy
* Cleanup of redis check functions

## 1.4
* Re-enable immediate stop-loss
* Better scalping rules
* Test strategy for scalp short
* DB changes for shorting strategy
* Drawdown for stag and prod environments
* Log cleanup

## 1.3.1
* Bugfix

## 1.3
* Add initial margin trading
* Make all methods margin-friendly
* Get more accurate fill-price from exchange
* Log both current price and actual fill price
* Separate stag/prod alerts in slack
* Fix some logging bugs
* Database changes with new field names
* Log critical when trade isn't logged in db
* Initial doc for config

## 1.2.1
* Fix pivit point bug in stag/prod
* Ensure redis expiry is consistent across environments
* Wait for candle to close for prod scalp stop-loss
* Notify if db update was unsuccessful
* Fix typo in prod docker-compose

## 1.2
* Scalp strategy for prod
* Create graphs inside each be container
* Updates to binance module
* Better formatting for slack balance
* Split notifications and alerts in slack
* Prep for adding margin & short trades
* Fix base amount in DB
* Ensure setting and retrieving open trades doesn't conflict
* Reduce deploy time and log to slack
* Log binance errors to slack

## 1.1
* New strategy using TSI/daily pivots
* Allow Closing a trade after a certain time
* Allow both immediate and candle close stop losses
* Manual Margin trading (long only)
* Add open trades alert to Slack
* Minor bug fixes

## 1.0
* Tweaking of testing parameters
* Get balance hourly on prod only
* Preparations of margin trades
* Checks for valid trading pairs
* Better error reporting
* Split containers by base currency
* Use forked local docker images
* Use cryptocompare module for TWT coin
* Get balance for phemex sub accounts
* Split slack messages per env

## 0.36
* Enable production trades
* Slack notifications for CI builds and tests
* Testing of 3m envelope strategy
* Small API/Cron fixes

## 0.35
* Fix trading pairs on API dashboard
* fixes to API and CRON
* Add production config

## 0.34
* Speed up API refresh
* Speed up initial download of historic data
* Add Phemex integration
* Verified staging trading pairs
* Slack integration for alerts and notifications
* Better parallel testing
* Better description when errors are captured
* Sort out currency precision when making/closing an order

## 0.33
* More explicit debug logging
* Add buy/sell rules and strategy names to API dashboard
* Fix bugs with initial prod run
* Uncouple test trade and test run
* Do an initial prod run immediately after collecting initial data
* Fix and sort naming convention for environments, hosts, tiers, and containers
* Add scatter graphs for calculating drawdown
* Sync pricing with exchange when initiating and closing a trade
* fix intervals between trades
* Better deploy script
* Cleanup c9e environments
* Add divisor var to decide how much to buy whilst supporting varying number of pairs
* Fix for margin balance to exclude debt
* Get monthly aggregated percentage test results per pair
* Avoid missing data in API by only updating when all data has been collected
* Add stop loss support for test data (which doesn't contain intermittent prices)

## 0.32
* Clean up c9e envs
* Add 5MA to stag
* New k8s job script and update template
* Add initial support for margin trading
* Fetch balance from margin wallet
* Update gechodriver for graphing
* Fix buy/sell from API
* Display buy/sell status in API dashboard
* Better logging for graphs and minor tweaks
* Ensure HOSTNAME var is added to docker compose

## 0.31
* Improve efficiency for Redis data
* Fix bug with non-aligned epoch times
* Fix missing data in graphs
* Add mysql dump to test runs
* Improved testing template

## 0.30
* Create Kubernetes Template for running test runs at scale
* Make docker containers k8s-friendly
* Script for collecting all associated data for test run
* New test configstore env for kubernetes

## 0.29
* Upgrade all bootstraps to use Python 3.7.0
* Upgrade requirements to match dependencies
* Add local test framework and enforce running with git hooks
* Use separate bootstrap scripts for dev/prod/docker
* Test cleanup

## 0.28
* Add local testing framework
* Reduce number of connections to DB and Redis
* Add Volume indicator to graphs
* Add profit factor to test runs
* Allow custom number of klines for test data
* Synchronize test and prod config

## 0.27
* Create graphs for all pairs in config
* Create thumbnails for API
* Add closed trades to API
* Expose matched buy/sell rules to API
* Better cron timings
* Download historic prices and indicators and populate redis/graph

## 0.26
* Testing of docker instance functionality
* Combine API and GC into single image
* Log directly to journald with preserved severity
* More cleanup of wasted diskspace on host and containers
* Fix of engine using incomplete data to populate redis in live mode
* Release script to pull latest version tag and deploy
* Add AWS S3 fuse package to non-test server for backups and other data

## 0.25
* Add api for displaying current open trades with ability to sell
* Add local install to travis tests
* Fix Crontabs with dates in path
* Fix webserver reverse proxy paths
* General cleanup

## 0.24
* Fix paths for nginx reverse proxy
* Allow scipts to determine open trades
* Limit trades by time since previous trade
* Fix relaive path for image building


