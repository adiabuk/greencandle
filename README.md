# Testing & Build status

| Build  	| Status 	|
|----	|----	|
|Main image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/greencandle)](https://hub.docker.com/repository/docker/amrox/greencandle)	|
|Mysql image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/gc-mysql)](https://hub.docker.com/repository/docker/amrox/gc-mysql)	|
|Redis image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/gc-redis)](https://hub.docker.com/repository/docker/amrox/gc-redis)	|
|Webserver image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/webserver)](https://hub.docker.com/repository/docker/amrox/webserver)	|
|Dashboard image |	[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/amrox/dashboard)](https://hub.docker.com/repository/docker/amrox/dashboard)	|
|Testing| [![Build Status](https://travis-ci.org/adiabuk/greencandle.svg?branch=master)](https://travis-ci.org/adiabuk/greencandle)|

# Releases

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


