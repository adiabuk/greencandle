# Releases

# 6.58.5
* fix typo

# 6.58.4
* only update redis if trade open was successful
* BUGFIX: cleanup db2 script not running
* check drain status before balance etc

# 6.58.3
* log amount source for trade open
* BUGFIX: use non-greedy substitution to avoid losing random redis keys
* BUGFIX: divisor causing double loans to fulfil max_trade
* don't re-fire data 1h slack alerts as often
* upgrade werkzeug and jinja2

# 6.58.2
* fix typo

# 6.58.1
* wait a few secs after closing trade before fetching new balance
* marker to easily locate trade-related logs in prod|data envs
* forward to 5m trades correct prod container
* add 50-period EMA to data env
* filter out zero volume pairs in touch strategy
* no slack for short step2 data env

# 6.58
* prod routes
* show slack alerts for first step data only
* add some missing forwarding rules and config
* fix rsi rules and intervals
* don't look for double balance when choosing balance over loan
* use correct log file for logwatch and logtailer
* generic filenames not working for logtailer
* compare rsi strategy with and without close rules
* new rsi short strategies
* tighten open rules for rsi

# 6.57
* cleanup and fix unit tests
* don't fail with slack msg when no trade avail to close
* don't try to send slack trade alert when config is empty
* capture timeout exception if stream container not available and continue with api call
* adjust prod timeout perc
* use per-env log file for UI logtailer
* add use_balance var to some prod containers
* reduce delay between intermittent checks
* always use 0 loan balance for test trades
* tweak rsi close rule
* increase rsi confirmation expiry & add 15m|30m containers
* get hourly crypto sentiment screenshots

# 6.56
* leave more candles in redis after db cleanup
* remove some 1m test containers and routes
* add new data=>prod route and tweak config
* cleanup redis db2 script and add to cron - all envs
* fix checking of sufficient balance in order module
* rename data channels and stratgy lookups to match
* retain only single bb data strategy and add second step to RSI
* add stream vars to api backend containers and use for intermittent checks
* reduce prod and test containers
* re-order stream container port mappings
* simplify prod_int_check and speedup
* replace macd strategy with rsi for 1m|5m|15m|30m for prod|test
* add working dir to all manual containers
* be more lenient with middle bb check

# 6.55
* add missing data api forward strategies
* update new strategy open rule
* add total net perc and current trade value to balances UI
* add previously removed close arg to display close window
* try to serve static files from nginx
* further increase time between trade notifs data env
* check balance when picking between loan and avail amt
* change of prod alerts
* fix typo in template path

# 6.54.3
* put html templates into static dir
* use proxy pass to avoid adding of internal port to url
* fix browspy http redirect
* increase time between trade alerts in data env
* add prefix to trade link

# 6.54.2
* add saved rules to new extras table
* capture candle closing well outside bb
* fix remaining broken urls with prefix
* fix dashboard healthcheck

# 6.54.1
* BUGFIX: revert removal of nginx config elements

# 6.54
* switch all logs to lowercase and enforce with custom module
* add log for extra rule processing
* remove all prod trade routes except extra
* single unified prefix for dashboard routes
* use correct key for delete button
* add saved rules to extras board
* change to unified nsca service names
* allow longer pair names in extras UI - 11 chars

# 6.53.2
* BUGFIX: use correct key when removing item from extras queue
* BUGFIX test test close script for short margin
* dont mix pair, and pair link
* use tv link for pair in extras ui table
* use epoch as extras redis key, and add to table as human-readable
* remove last step2 old strategy slack notifications
* reduce verbosity of zero-loan trade notification
* dont fail deployments on envs without frontend

# 6.53.1
* add volumes for new per-env log files - all envs
* BUGFIX: avoid 302 for logtailer as it adds port to url
* BUGFIX: use adjusted amount for short trade when no loan used

# 6.53
* Use syslog facilities for separating env logs
* reduce slack notifications
* increase interval between scheduled task runs
* remove 12h config & prod containers
* 5th open rule for bb touch upper|lower
* use stochrsi for 1h data old strategy
* separate 1h notifs into separate slack channel
* use balance for margin manual prod trades
* add another missing 15m test config dir

# 6.52.2
* don't repay prod loans periodically
* fix html values in extras UI
* use correct redis/routing vars for new analyse containers

# 6.52.1
* add missing 15m|30m config in data|test envs
* allow extras to be routed to alert
* ensure all fields are present in redis
* allow for additional open|close rule in config
* add new intervals to extras UI

# 6.52
* dont open new window when closing trade online
* remove all 12h containers and introduce 15m|30m
* add tpsl and usd amt to payload before forwarding
* pass routes from router_config to ui
* split prod long|short extra strategies
* missing data long3 container
* add ability to remove existing trade rule from redis (db6)
* check extra rules in new single container and delete rule after match
* extras UI fofor adding ad-hoc open|close triggers for any env

# 6.51.3
* only show combined long/short entries in trade UI
* BUGFIX:add individual routes for manual trades
* BUGFIX: no result if exception caught
* template for extras trade UI
* confirmation rules for open|close old strategy step2

# 6.51.2
* don't open trade with >50 stop_loss
* use f-strings for error logging for slack notifs
* all alert routing for step2-old strategy
* fix dc deps
* add new forwarding rule
* forward rule for old strategy
* no tpsl for stag env
* touch check file at bottom of analyser loop

# 6.51.1
* Fixes to unittests
* only use upper bb for new atrp rule
* BUGFIX: no stop loss if value <= 0
* add rsi to agg UI

# 6.51
* alert env var superfluous in data env
* Revert "adjust test env tpsl"
* remove test alerts
* alerts from data strategy
* name lookup for new step 2 containers
* don't alert if short trade not open
* don't send drain msg to slack
* recreate args dict, removing empty
* fix cmd line args check
* keep old strategies for reference
* fix bb high/low check against middle
* add more info to log
* new data strategy - atrp increase 1m|5m
* remove unused data containers
* readd simplified step2 strategy
* combine data strategies and add stochrsi|atrp checks
* add reversal check rule to config
* don't send all data to function
* allow longer args in UI
* use all data in main agg function
* loop through list and get last 10 items
* test artp agg of last 10 equal values
* adjust tpsl for prod long term trades
* add config for prod manual trades
* add bashrc to all data containers
* reorder web menu items
* add open|close to trade alert log

# 6.50.1
* increase verbosity of some errors
* BUGFIX: no repay_result if operation resulted in exception
* return True, for soft errors to not spam slack with alerts
* reduce TP and SL for 1m|5m main test strategy
* BUGFIX: missing quote in anchor link
* reintroduce alternate MACD containers data env

# 6.50
* return empty list if no trades, not NoneType
* run close_all as arg only
* Run commands with args from UI
* add name filter to close_trade script
* add MACD upper timeframes assocs to test env
* add missing prod router assocs
* match prod config to test
* allow list of open trades to be filtered by name
* use middle bb for close of bb & macd trades
* only send slack notif for trade opens
* fix anchor link target

# 6.49.1
* BUGFIX: entry not being removed from redis set & increase log verbosity
* remove alternate MACD containers
* add macd xover close rule with RSI
* BUGFIX: fix anchor link for dashboard
* add RSI as 3rd close rule to main 2step strategy

# 6.49
* increase mem limit for data env mysql
* increase expiry of redis db3 set contents
* filter out pairs with recent 0 trades in all data notifs
* add empty_count to data dashboard
* no of df rows with no trades as agg data
* collect more agg data for aggregrate
* add ATR perc to data env and dashboard
* test new ATR perc method and add docs
* declare dataframes before open|close functions
* increase bbperc trigger to 2
* add logging when adding/removing to redis set
* avoid redis set dupes with different expiry times
* check for expiry on redis_trades only
* add new test containers and router assocs
* add alternate MACD check
* Revert "only forward to single redis db"
* update drawup/down on trade close
* log error when unable to fetch info of closed trade
* git commit hash from git for start of deployment

# 6.48
* only forward trades to single redis db
* expire redis set members if not used after given time
* remove unused config, strategies and config items
* combine step1/step2 slack channels
* wait for stream before fetching data
* move stream-checker to get containers
* restart policy for stream containers only on failure
* don't restart stream containers on each deployment
* add open|close result to trade forward notif
* BUGFIX: initial MACD data out of sync
* ensure bbperc_diff agg always returns numerical for parsing
* use fstring for error level logging
* increase data env trigger verbosity
* raise log severity for critical errors
* fix reopen_trade in analyser
* use 443 stream port
* BUGFIX: missing trade param for spot trade and undeclared du/dd
* add du/dd to slack trade notif
* increase mem limit for get containers
* ensure we return at least the specified number of candles, and speed up
* increase no_of_klines when increasing date range
* account for MACD histogram when creating graph
* add favicon for alarm env
* increase deploy time nagios downtime

# 6.47
* add test env 12h and 4h containers and adjust all tpsl
* increase log verbosity when no candles downloaded
* remove de-listed pair PERLUSDT
* custom favicon for each env
* detect non-existent df, as well as empty
* add pair to redis log
* check num of trades in new strategy
* short url without host for web
* ensure we capture extra new argument in list of trades when closing
* BUGFIX: et slice, not index of df list
* fix data strategy rules bbperc
* big change in bbperc strategy
* add prod lt router entries and assocs
* add additional timeframe for macd check

# 6.46
* add prod long term trade containers
* allow borrow to be turned off using lock file
* pass override max_usd value through api
* add usd amt to trade dashboard
* calculate usd value separately in cross balance
* no borrow result if exception raised
* complete remaining api forwards to test env with alerts
* add missing upper timeframe prod config

# 6.45
* log deployment start/finish
* add prod forwarding rules for bb & MACD
* add close rules for bbperc/direction trades
* still add data to df even if no prev data
* ensure pair is being removed from redis after trade is opened
* use correct 12h api forwarding rule
* group daily profit view by both open and close times
* remove local volume from get containers
* fix router config
* move macd strategy to separate slack channel
* set check var for new containers
* add new strategy name for slack
* remove unused router and forward rules
* replace HA check with MACD check
* loosen restrictions for MACD rule
* remove de-listed asset
* alert for 1m test
* get more candles if empty dataframe (req'd for some small timeframe pairs)

# 6.44
* forward bbperc to test only
* create and forward MACD trade closes to test env
* update balance in dashboard every 10mins
* check avg candle size in MACD strategy
* revert removal of RSI/BB until implementation of celery
* fix ordering for forward rule checker
* remove rsi/bbperc from macd rule and tweak forwarding rules

# 6.43
* update macd doc
* remove higher timeframe macd analysis containers
* update pulse socket location to use system service and use root
* add missing usd value in balance
* add diff between macd and signal agg data
* sort columns in agg table
* allow an extra min for lock file healthcheck
* remove delisted asset TOMO
* add additional pair for analysis
* add alerts for macd and bb/distance triggers
* add MACD and histogram data analysis with volume & RSI
* add macd indicator with with histogram

# 6.42
* Update python/debian alert base image
* Switch from alsa to pulseaudio as non-root user for alert
* don't include alert image in automated builds
* move alerting from test to stag

# 6.41
* add bbperc ind to agg data
* add new user in alert container
* additional audio alerts
* alert on step1 data only
* Bump urllib3 from 2.0.3 to 2.0.7

# 6.40
* reloading live sheet should reload fresh data
* update db schema with charset and view changes
* add day of week to profit_daily db view
* use tv link for aggregate data pair

# 6.39
* alert when trades reach certain profit
* column name & ordering for open_trades and prod balance
* increase mem limit again for api containers
* properly kill docker containers after HC fail
* Bump urllib3 from 2.0.3 to 2.0.6
* increase analyser mem limit to 1g
* restart container if api healthchecks fail
* check bb_20 in upper timeframes and remove bb_200 middle check
* fix mysql char set - remove refs to Swedish
* fix small dust conversion script - unreachable code
* add missing header in error template

# 6.38
* add balances to live UI table and remove balance cron
* update db schema
* no profit filter by default
* daily commission view
* risk is 999 (inf) if there are no debts
* add net_perc to dashboard
* filter out profit views based on name

# 6.37
* combine UI spreadsheets into single page
* add error jinja2 template file with message param
* reduce some logging
* always return absolute values for drawup/drawdown

# 6.36
* remove unused lint exception
* add tpsl and draw up/down to live table UI
* get correct reversal string
* enable default table ordering in UI
* separate gc logs out of syslog and use greencandle.log
* add additional info to direction change notif
* ensure all data pairs have trade type in mysql and redis
* dont trigger close if we reversed direction
* mysql function to reopen a trade
* add slack icon and direction change string to notif
* add to single redis db with long|short key
* catch all binance exceptions from trade operations
* fix deps for direction containers
* add slack channel for new data containers
* wait for 3rd HA candle before triggering trade as most recent candle is incomplete
* add direction container configs
* allow intermediate containers for checking higher timeframes
* improvements to close-trade checker
* remove applied db changes
* downgrade binance log to debug

# 6.35
* don't blanket-catch exceptions in orders mod
* fix old drawup|drawdown values not being removed before after trade
* re-add comment field in profit view and update schema
* allow getting current drawup/drawdown and tpsl from outside context
* fix data env docker compose yaml syntax

# 6.34
* don't reformat live page for mobile
* remove applied db changes
* remove unused containers in data/test env
* use gross BNB when bnb and close cheker scripts
* don't catch BinanceException in binance module as we catch it in orders
* don't disable concurrent builds at top level - this queues when we run unit tests

# 6.33
* make UI login session last longer
* cast perc/net_perc as decimal to allow sorting of db views
* update db schema with latest changes
* add comment field to profit view from trades table
* don't skip interest repayments due to open_trade
* fix typerror, num of redis items arg should be int
* lower stop_loss on any3 test strategy & prod env

# 6.32
* tighter step1 open rules checking open outside bb & (stoch)RSI levels
* fix jinja syntax error
* capture binance exception for borrow/repay loans

# 6.31.3
* separate new data rules and forward to test env

# 6.31.2
* increase mem limit for all cron containers
* access graph images directly from nginx
* allow creating chart with ohlc only
* update colours for chart and candles to be more visible in thumbnail
* disable caching in browsers to ensure fresh dynamic data
* allow redis cleanup script to take num arg and limit to 60 tfs
* create graph function to parse args to enable calling with dict as well as cmd line

# 6.31.1
* remove deprecated db tables, views, and code using open_trades table
* fix trade scope functions and update unit test

# 6.31
* deprecate trade status cron and open_trades table
* calculate perc in realtime for dash and close-trade script
* need much more ram for data cron to take snapshots
* auto scroll log tailer and remove top line/remove page refresh
* add installed version info to web portal title
* don't use loan of we have 3x max trade balance avail
* reduce verbosity of healthcheck logs
* remove encrypted values from unittests
* update redis to latest version 7.2.0
* disable redis persistence when testing
* tweak healthcheck intervals and reduce mysql/nginx procs
* fix close link and perc (for short trades)
* use sh.tail rather than opening up whole log file
* add close link and shortname to open trades dash
* add sh pip to reqs and python base image
* add stream var to all containers requiring access to live prices
* live data dashboard with current trade info
* enable data1 trade db storage and close signals
* fix and stagger cron entries
* add curl to backend_api healthcheck
* new data strategy with tweaks to close_rule

# 6.30
* add new data env with additional RSI close rule
* more logging in assocs unit test
* cleanup of tests inc unused vars/imports etc
* add cron syntax tests for all envs
* round binance BTC value for notif
* don't call binance dust function if no dustable items to convert
* remove old/unused cron script from stag cron
* more mem for dashboard containers to allow running of scripts without OOM
* cleanup profit monthly db view
* differentiate between interest|borrowed debts in logs
* add dust loan/amounts to cron to convert to USDT/BNB and run every 7 hours
* run interest|borrowed repayments separately
* add record of commission and interest payment to db
* create lib functions for fetching loan/commission for re-use
* binance methods to fetch/convert small loans to USDT
* add dev port forwarding

# 6.29
* don't fail api healthcheck if too many procs due to rq fork
* add week commencing to profit weekly view
* open open trades summary view
* fix test env healthcheck intervals
* add API healthcheck script for backend api & rq procs in all envs
* add VPN_IP to all dashboard containers to allow trade status script to run from UI
* add risk/repay debt scripts to dashboard
* add new daily profit view and daily breakdown by open/close
* add gross value to cross balance dict to allow prod trades to auto close/repay
* wait for close to cross bb before sending close signal from data env
* clear all debts not in trade every 10mins
* get cross margin risk and push to nagios with performance data for graphing
* wait for an extra HA candle before sending open trade
* only send nagios data trade alert in selected containers
* send data trade alerts to nagios
* test json config integrity during build
* catch exception when we don't have a balance for given asset

# 6.28.2
* Lint rules

# 6.28.1
* allow running repay debts script with list arg display actions without executing repayments
* get gross balance from exchange (inc loan) in order to calc repayment and use to repay
* ensure both hourly and daily queries return data in cron script
* fix json syntax in data env/get_data containers

# 6.28
* set default clack channel for data env
* only repay as much as we can from avail bal
* catch typeerror in supertrend
* close data trade when we have a new open signal if checking redis and mysql
* Forward 5m trades to prod env
* remove STX data strategy
* keep less backups
* slim down stag env
* fix test_close fstring
* fix unicode in config

# 6.27
* update prod tpsls
* ensure logs have sufficient info to trace
* reorganise slack notifs for test env
* close trade if supertrend flips to opposite direction
* wait for increasing candle size before opening trade
* add one more item to loop through when fetching indicator/candles
* filter out trade notifs
* use 5m config from 1m test any3 strategy
* reduce alarms
* speed up deployments
* allow trades with less volume for HA-flip
* check both current and previous HA candles before flip
* fix incorrect open rule will never fire
* less noisy HA flip rules
* fix trades not being closed due to undefined fstring

# 6.26
* use decorated func name for exception name in slack
* don't run collect_pairs script in test or prod cron
* close data short trades a little earlier by reducing bbperc value
* add bbperc close rule
* use open_pairs instead of all
* modify bbperc/HA strategy and test tpsl
* ensure alert don't go to default slack channel if empty
* enable close trade notifs in data HA containers
* start db with correct interval to ensure open|close of data trade notifs
* increase cron mem limit
* add 1 more open|close rule in data env
* add and test close_rules in dev env
* get net profit|perc from db for trade close notifs
* separate out data=>prod routes to allow direction drain
* download link for current data from dashboard as csv/excel
* reduce no of HA flip notifs
* combine data containers which don't use redis
* log amount of slippage margin available on trade open
* don't repay debts used for open trade

# 6.25
* forward single rule to prod
* remove quotes from env vars in docker compose files
* separate redis db for different strategies and allow forwarding to multiple dbs
* override css width to show more data fields in data dashboard

# 6.24
* fix today's profix query following view removal
* add sum of last x candles to data dashboard
* rename agg var for clarity
* fix container names for latest data strategy short
* fix heiken ashi sequencing for initial data run
* add heiken ashi direction flip containers and check direction using STX

# 6.23
* extend time between trades for new data strategy
* add HA match name to analyser list
* add bb size check to data size rules
* only trigger data alerts where size between upper|lower bb is higher than 1%
* forward HA to new test env
* specify which containers to delete stage2 pairs from redis
* add open_time to close_all script output
* data containers for heiken ashi check after step1
* add dev router, analyser, and test rules
* add heiken ashi to data env
* add graph support for heiken ashi
* new algorithm for heiken ashi and updated docs
* min 50 trades in candle for all strategies
* fix HA keys
* update pandas-ta

# 6.22
* don't ignore last item in agg
* create lock dir if it doesn't exist
* split 1m get_data containers into 4 to speed up each run
* don't re-define open var in engine
* remove old agg script
* cleanup redis data using pairs from config to ensure none are missed
* use previous 5 candles, not inc current for avg size
* Add agg data to slack output
* fetch agg data as part of get_data container to ensure it's in sync with candles and indicators

# 6.21
* check that close time exists for a pair as higher timeframes might not have closed when starting
* increase ram to data env redis
* use both updated and recent candles together depending on which is more recent and not dupe
* add stream link to dev manual container
* use ProcessPoolExecutor for parallel procs
* various changes to dev environment - slack, config, docker links
* config for redis
* manual container for dev env
* add heiken ashi candles to engine for testing
* check current direction with previous candle close in data strategy
* convert currencies to USD, not BTC for balance as some coins don't have a BTC pairing

# 6.20
* use first element of STX for comparision
* rename and consolidate data slack channels
* add short candle-size data containers and add separate config for each timeframe short & long
* use new location for docker healthchecks and tidy up dir
* ensure we are on right side of trend for candle-size longs by using supertrend
* add logging to aggregate container for debugging
* add new match names to analyse script
* calculate candle increase differently with lower start size
* calculate candle size aggregate using only current candle, not previous
* add human-readable open-time to agg data for debugging
* fix syntax error reversion
* more size rule tweaks

# 6.19.1
* filter out low vol pairs in candle size rules
* tweak candle size rule
* empty string when match name not found
* fix syntax errors in agg script
* skip opening trade if unable to get candles
* avoid divide by zero error and cleanup size rules
* margin amount to use based on stop_loss to ensure enough to repay
* remove deprecated agg script

# 6.19
* use 6dp for candle size perc and account for 0 candle size
* add missing agg item in redis/dashboard
* don't automatically reload data page after 60 secs
* new data rules and containers for sudden increase in candlesize
* combine both aggregate modules and sort data in dashboard
* clear applied db changes

# 6.18
* use stdout for cron logging
* forward long/short data trades separately to allow separate route draining
* updated db schema from recent changes
* add second batch of prod any containers with routing

# 6.17
* add router level drain
* profitable open_trades view
* pass request details to binance exception
* add ncsa pip to containers, jenkins image and base image
* remove obsolete db views
* table naming convention
* submit avail trade slots to nagios as passive check
* re-order profit view and profitable_daily views
* add event to db comments field
* add comments field to trades table
* delete all new views/procs if exist before recreating
* refresh db views and procedures
* need to combine both long and short values of day's profit
* add prod 5m router config
* create c9e output dir for processed templates in redis container

# 6.16
* forward 1h trades to prod and adjust tpsl
* run dev env using redis config file using entryfile
* add c9e to redis image
* increase nagios downtime for builds
* increase max trades for 5m/1m containers

# 6.15.1
* repay_result is normally empty/NoneType if all is good
* missing bracket inside fstring

# 6.15
* fix dev env links
* match correct drain file
* fix forwarding strategy name
* tweak distance data rule
* separate dev env from other envs
* add current default redis config from running container
* add nagios downtime during build process
* fix format string for slack output

# 6.14
* add container number to analyser proc title
* increase analyser containers to 500M
* ability to drain specific container/strategy as well as entire env
* add and configure 5m prod rules
* make initial rules fire quicker, and use RSI for confirmation
* add RSI with default values to data env
* change alerting rules

# 6.13
* use correct value for supertrend long
* no need to cancel opposite opportunity, this is done at trade-open
* remove EMA rules, leaving only supertrend for 2nd level data
* change tpsl+trailing for test2 env
* increase supertrend multiplier in data env to not get stopped out
* fix fsting in scope script
* add initial default redis config
* skip containers that don't exist when getting short name
* use cached mp3 for portions of text to avoid re-requesting
* use tag for alert image
* retag alert image
* insert pause in audio between trading pair and text
* prune alerts more
* option to use google for voice syn
* alert only from data env
* alarm container will be created separately, not part of main build
* allow forwarding to router and to redis
* new replica test envs for 1m,5m,1h

# 6.12
* reduce data env deploy time
* install ta-lib in base image from tar and upgrade in reqs file
* remove deprecated bootstrap scripts
* move gc image steps to base image to speed up build/testing
* data env makes more use of redis - increase mem
* 5sec pause after fetching limited no of pairs from redis, otherwise 1sec
* use tmpfs for mysql/redis in jenkins/unit DC files
* use tmpfs for /srv when building/testing
* stx needs a closed candle so use last full candle
* add healthchecks for all containers in all envs
* change intermittent start/end logs to debug
* remove trade from db4 redis if one exists in opposite direction
* reduce data EMA length
* use db4 for pairs to pass pair from one strategy to the next

# 6.11
* save time and resources by only analysing pairs we care about in this loop
* no longer need to delete redis data after release due to reduced startup times
* ensure we don't miss a trade for preexisting conditions that triggered earlier
* require login for data UI
* only remove pair from redis if we have a confirmed 'open' match
* allow sufficient mem for manual containers
* use redis to forward trades between multiple analysers in data env before forwarding

# 6.10.1
* BUGFIX: don't forward every trade

# 6.10
* shorten text to alarm env
* use output directory for all mp3s
* refactor API forwarding rules to allow multiple forwards
* script to create mp3 using google and amazon
* alerts module lib file for future improvements
* don't routinely create graphs with cron
* change unsafe port for data env UI

# 6.9
* allow generous memory allocations for log/api/cron/analyser containers
* remove old legacy code and debug comments
* fix boolean check in prod run
* don't try to analyse pairs without any data
* remove unused indicator in data env
* combine api calls to single one per prod run

# 6.8
* typo in router config causing missed trades
* fix prod 1h long name
* add num of trades/candle to agg data/dashboard
* capture failed db trade update
* improve formatting of slack msg

# 6.7
* repay BNB in prod every hour
* allow specifying single asset to be repaid
* matching 1m router keys to fix close link, and add alert
* prod shortnames in DC file need to match router config
* get prod trade status more frequently
* check for zero-trade candles in all data strategies
* catch all errors with borrowing funds

# 6.6
* don't alert if no trades/volume for current candle
* send forwarded trades from data env to alarm env
* increase timeout to calls from router
* wait at least 12h between 12h trade alerts
* max volume for alert
* only add alarm name to audio string if it hasn't already been set
* need to convert net-perc to float to compare

# 6.5
* single api queue for stag and prod
* use explicit trade_direction for sub configs, don't rely on inheritance
* fix env and router config for stag
* remove unused stag dirs
* disable trend on all stag containers
* cosmetic syntax fix in sql code
* fix redis values being updated with values from previous loop if data fetching fails

# 6.4
* remove all but 1h/1m cross containers in prod
* use a single set of pairs for entire data env for simplicity
* move bb rule to second container for visibility
* keep 2% of borrowed & available funds when trading for slippage
* use more of avail balance rather than loan in prod
* use different slack channel for second data analyse containers
* further increase timeout to stream containers

# 6.3
* move api_forward config to second analyse containers
* STX needs to wait for candle close
* increase timeout to stream container request
* STX data point alignment
* change STX settings
* tweak ema rules
* write match string to log
* display match name instead of number in notif
* return number instead of None for distance agg
* ensure we eval all rules during each run
* remove store-in-db flag in data env
* disable slack_trades throughout data env
* try to avoid strings in agg data - use numerical
* remove non-trading pair
* insure all containers have correct name and interval
* add slack channels to get containers
* remove some stag containers
* reorganise data c9e
* General cleanup and removal of unused code
* add stx_diff to agg data
* increase distance agg threshold on >1m containers
* add proctitle pip as req for alert

# 6.2
* Switch to using f-strings
* Multitude of lint fixes following recent updates
* Log/slack output formatting fixes
* only use error level logging for exceptions
* check if tpsl is empty string or None
* get mepoch from current time if unable to fetch from redis
* remove unused args, pararms, and vars
* add proctitle to all executables started from docker entryfile
* reduce default max trades to 4 in prod 1m, unless overridden
* disable trailing SL for prod 1h
* ensure we check if trailing SL is enabled
* remove print statements from agg script
* add "all" data table in data env UI
* discard old jenkins builds
* only keep 3 days of mysql backups & reports
* run agg data continuously in separate container
* get agg data from redis directly for dashboard and remove csv creation

# 6.1
* add data agg analysers
* update docker and websockets python versions

# 6.0
* Security updates for python scipy
* Security updates for python numpy
* Security update for python redis
* Security update for python flask
* Update python to 3.9 and recreate base/jenkins docker images
* Various updates for dependency resolution
* Various fixes to account for libray changes
* remove ipython hack in dockerentry file for manual containers
* insure using right version of urllib3
* Removal of unused test code relating to git pre-hook and checksum
* Account for new lint rules from updated pylint packages
* reduce base img size by merging docker layers
* remove pip hackyness and install required verions in base image
* fix per env api container entrypoints
* change EMA_8 to EMA_13 in data env

# 5.36
* fix prod api container entrypoints
* add more logging for data analyser when opening/closing trades
* greatly increase no of initial 1m candles to account for low volume pairs
* fix long2 open_rule1 bbperc
* add missing pairs from BTC containers
* raise error when unable to fetch stream for given pair
* increase bbperc short trigger on all data containers
* print direction when closing trade in data env
* reduce logging by downgrading to debug and disabling noisy stream container GET output
* turn off debugging for test env
* code cleanup

# 5.35
* add candle size to data ema rule
* fix data long2 open rule
* update active trades before closing
* fix bb_size agg to use new bb list
* add container name to data trade notification
* fix perc comparision and display value in close script
* rename ema channels in data env
* separate slack channel for noisy notifications
* reduce data env deploy delay
* single trade-status cron invocation for test env

# 5.34.1
* Lint fixes

# 5.34
* close all trades above threshold from cmdline & dashboard
* Use open_time as redis index and graphs/event dates
* ensure we have enough data in 1m, accounting for empty candles
* properly loop through last x first-run items in engine
* use min number of runs for data analyser
* increase number of lookback elements in res list
* continue making graph on empty supertrend df
* create 3 seperate long/short data 1m containers and remove temp cron
* fix indicator sync when using live data
* update indicators doc
* never alter opentime/index when fetching indicator data as this overwrites existing data in scheme
* update plotly to latest version to overcome bug displaying ohlc candle graphs
* remove vol MA method as not required
* Update moving averages method, and verified values match tradingview
* cleanup graph lib
* tweak tp/sl for 1m test containers
* don't skip entire dict if some values are None
* convert values to string as redis doesn't like None
* try to turn agg data to float for parsing/comparision
* make agg data available to analyser and add to 1m rules
* remove spaces from agg tsv files for column parsing
* add agg data to redis db3
* fix selenium tests
* ensure we reset drawup/drawdown on new trade to avoid incorrect data on trade close
* no max trades for in data env
* clear more redis dbs in clear_redis script
* add link to router from data cron container
* add current candle size to agg data
* add missing pair in 4h/1h get_data containers
* look for bbperc reversal in data env
* add non btc/usdt pairs to btc get containers

# 5.33
* no longer need to run analyser in threads as process has significantly faster
* reduce logging in each analyser loop
* add max_connections arg to mysql
* speed up data analysis by only checking rules in data env (reduce run by 7mins)
* remove bb test containers
* backend api containers need more memory for rq
* update rq version
* change data supertrend settings

# 5.32.1
* ensure we shutdown thread pools
* increase mem limit 100->200
* only versioned tags are releases

# 5.32
* update indicator doc for supertrend
* add supertrend value and direction for graph plotting and reformat plot
* reset graph items for next loop iter to avoid duplicate plots
* line up supertrend data with tradingview graph
* don't use ctrl chars in DC output
* use lockfile to ensure crons don't overlap
* Increase any2 test take-profit to 2
* Allow for null drawdown/drawup for data env which aren't real trades
* Use margin for data env to allow for short trade notifs with close
* remove low volume pair from lower timeframes
* don't send usual trade alerts in data env
* add/enable data close trades for 1m containers only
* store data trades in db to allow for close notifications
* interval for analyse needs to be higher
* add memory limits to containers
* remove cadvisor containers from all envs
* remove unused strategy from stag env
* Specify project when deploying to avoid interference with other envs
* docs for verified indicators
* add human readable time to redis entries
* reduce time between trades in data env
* add second rule in data upper timeframes with bb_12
* show matching trade rules in data notification
* fix DC extra hosts syntax

# 5.31
* Update pandas to latest for efficiency
* cleanup unused dataframe objects and garbage collect
* remove stochrsi data rules
* no need to back fill indicator data for lower timeframes (1m/5m)
* add stream to stag data hosts file

# 5.30.1
* stag proxy no long required
* move stag slack config to upper level to enable slack for all containers
* remove debug print statement
* don't pop items from header in trade status notifications
* catch/ignore Nan values in StochRSI agg data
* upper time frames take longer for each loop, fix healthcheck

# 5.30
* fix 12h usdt name
* display done msg if no exceptions
* stochrsi settings doc
* add stochrsi k to open/short data rules
* make bb graph with with new notations
* rename to meaningful var name for pandas series
* use custom stochrsi method to match tv data
* use data tupple function to get get correct amount of rows
* remove scheduler as it doesn't run in background
* speed up get/analyse data
* add middle bb aggregate to all csv/tsv
* log when forwarding trade from data env
* fix aggregate header
* use fixed header each time in loop
* add indicator unit test
* get distance to middle bb agg data
* direction required for trade link and tpsl calc
* get env from c9e not env var and remove all refs to $HOST
* use correct CONFIG_ENV for 5m containers

# 5.29
* make isolated balance disabled by default
* add 5m and 1h forward rule
* alerting for 1h test only
* remove unused column header

# 5.28.2
* wait 30 secs after deploying a get-container
* initial indicator doc
* catch attribute error
* catch all binance exceptions when converting to json
* use https proxy
* remove unused data env container links

# 5.28.1
* Capture json decode error when binance returns HTML error
* Remove proxy from test env

# 5.28
* Fix stag entrypoint causing container restart loop
* new testing API keys
* add logging and exception handling to binance
* merge seperate binance module
* add tpsl to trade status output
* add seperate containers for btc/usdt data upper timeframes
* add new btc data pairs and split btc/usdt in higher timeframes
* delete broken symlinks in current agg dir
* fix data cron healthcheck
* change data rules
* add 1h start period to analyse healthchecks to account for get_data wait time
* increase analyse container healthcheck interval
* further reduce initial data klines, but leave more during cleanup
* ensure we have an index for supertrend
* unable to parse index for rate_indicator
* use new bb notation in agg data and fix csv output header
* add u/m/l as list in a single dict key
* remove debug logging
* cleanup config
* add 2nd higher bb for data envs and add to agg data
* get all 3 bollinger bands with a single request
* update alerts doc
* more cron cleanup/tidy
* remove non-trading pair
* further increase higher timeframe stream healthcheck thresholds
* cleanup cron template
* only supress audio alert alert when drain file is present
* run alert webbhook unbuffered for print statements
* add logging driver for alert container
* cleanup old mysql backups after 7 days
* get agg candle size from new script
* get min/max/avg candle size perc over last x candles
* trim trailing zeros from open/close prices in db

# 5.27
* increase timeout and interval of 12h/4h stream healthchecks
* round open trade current percs
* increase stream healthcheck interval/timeout thresholds
* log to slack when ws socket is opened or closed
* Bump requests from 2.28.2 to 2.31.0
* ensure healthchecks don't use proxy
* add stream healthchecks
* fix agg data cleanup cron
* Don't run old get_data cron
* archive agg files older than 3mins, and delete after a week

# 5.26
* aggrgate data for supertrend direction change
* remove delisted pairs
* update websockets module and try to reconnect after failure
* turn websocket exception into string for logging
* move data indicator config to top level
* test tpsl in trade ui
* test container name matching c9e name
* remove unused stag containers
* short name container unit test
* add stream api port mappings for monitoring

# 5.25.1
* fix broken open rule check
* 30m between 1m trade alerts
* fix analyse data entrypoint
* use logging module for websockets
* add filter arg to links_to_dict function
* match data names to DC names
* add shortname assocs for stag containers
* aggregate column ordering
* use naming/links convention for data env

# 5.25
* bump flask and jinja2 versions for alert module security fix
* clear redis db1 api queues on env startup
* delete bad redis keys from db2
* always add draw up/down in context even if one doesn't exist
* use consistent delimiter and ordering for redis keys
* remove space in sql statement when updating open_trades table
* don't get/set tpsl or update draw up/down if no trade in context
* ensure drawup/down function outputs match
* script to get current drawup/drawdown
* use short name for redis tpsl & draws
* allow drawdown to get passed interval
* speed up get_status by getting prices only once
* catch request timeout exception

# 5.24.1
* code syntax fix

# 5.24
* allow for larger pair strings in db & update db schema
* refresh data page periodically
* revert devenv ports
* remove unused config
* reduce frequency of data alerts
* use engine instance vars instead of passing same data & use renamed df for supertrend
* alert image build steps
* disable alert threading so audio doesn't overlap and disable manual trade alerts
* change ordering of all data spreadsheet and fix column names
* only alert when calling combined strategies
* fix alarm forwarding in router and only forward analysed trades once

# 5.23
* correct agg column names
* fix aggregate type error with bbperc ind
* add spreadsheets to web/dashboard
* move sorting of df columns from Engine to Runner class
* slow down fetching of data a little
* reduce no of candles for data env
* raise websocket errors, but catch flask errors
* fix stag container

# 5.22
* get closed candles separately from recent data and sort dataframe
* format aggregated indicator values
* get all data continuously now that we're using websockets
* use stream instead of api for data updates
* stream data using websockets
* don't send prices to Engine instantiation
* bump binance version for path logging
* pass binance prices to helper functions
* fix ordering on /trade page
* add complete aggregate data sheet
* Add proxy for some containers, and exclude local http/https calls
* fix stag env
* aggregate all data into a single spreadsheet
* use functions for each aggregation and cleanup script

# 5.21.1
* lint fix
* simplify stochrsi logger msg outside try block

# 5.21
* get bb size agg using data cron
* get aggregate size between bollinger bands
* get lower timeframe data continuously
* use web proxy for test containers and higher timeframe data containers
* fix stag webserver cmd line args
* forward alerts to correct container
* use absolute values for distance agg result
* script to get open pairs in current container's scope
* catch stochrsi exceptions
* run agg scripts every minute
* fix manual container setuptools deps
* enable slack alerts for get_data containers
* all agg intervals on seperate line for sorting
* fix candle size aggregate
* fix agg float formatting
* get complete list of pairs for agg

# 5.20
* don't use perc for bboerc_diff
* remove delisted pair
* get all data every minute, whilst keeping analysis to candle close
* use api and queue together in prod/per envs
* fix stag entrypoints
* quote entrypoint args for all envs and cleanup
* use decimal type for perc/net_perc to get accurate min/max values & update schema
* fix broken api after container restart
* use test env ports for dev env
* increase max_trades for test env
* add seperate alarm env and update assocs/forwarding rules
* comments for aggregated data code
* send start/end initial prod run to data channel
* remove 5m and 1m pairs with insufficient volume
* add new cross USDT pairs to data env
* timeframe arg for open graphs script
* support 12h timeframes in binance
* use localhost if no VPN_IP set
* add interval to TV link for open/close alerts
* add 12h data containers
* cleanup container order in docker-compose
* add agg data volume/bbperc/flatline stochrsi/candle size
* exclude forward from container lookup
* aggrgate csv/tsv files with date for each run and create symlinks to most recent
* get open_price in trade_status, not amount
* increase timeout
* reintroduce installed flag for docker entryfile

# 5.19
* small routing fixes
* add forwarding strategy to router
* check if env var is in the payload
* change forwarding strategy in dev env
* matching logs for short trades
* use https when forwarding to different env
* display full payload in log
* correct api forward rule for data env
* more logging for api router
* use proper api token for data env
* add data for bb distance script
* fix router config syntax
* get unique set of pairs from redis 1m to use in aggregate csv script
* turn on forwarding for data 1m
* add data env csv creation cron
* gather data more often than analysing
* use router for all routing
* initial script to aggredate data env data
* never get just one candle even with intermittant checks
* remove applied db changes

# 5.18
* increase healthcheck timeouts
* adjust non averaged profits
* ensure action is a string regardless of contents
* increase size of perc_diff function return value and adjust tests
* add current epoch to each redis entry
* fix get_data docker healthchecks

# 5.17.1
* Fix failing api trades in test mode

# 5.17
* populate good pairs from correct strategy
* convert to uppercase after we ensure action isn't numerical
* only insert good pairs into table if available
* only avoid dupe trades in current direction
* only remove redis drawdown/drawup & tpsl from one place
* allow open/close on combined strategies
* remove forwarding containers in stag
* try not to overlap trade_status runs
* extend max time in trade for prod
* allow converting months and years into seconds

# 5.16.2
* only remove tpsl from redis after order has successfully closed
* use correct slack channel for test env trades
* allow multiple orders for race condition when opening trade in opposite direction
* improve lint score of orders module
* cleanup config
* capture sql command during sql exception
* add stochrsi to data envs

# 5.16.1
* fix get_trade_status formatting & name retrieval
* clear applied db changes
* updated db schema
* fix slack channel assignments

# 5.16
* remove staging inwcoin
* use internal router alias and remove HOST_IP var
* revert alert port to 20000
* catch exception when unable to get candles
* attempt to forward data audio alert
* Remove data env bridge networking and dns overrides
* add /var/local volume for alert lock files
* Fix Selenium tests
* fix per env names

# 5.15
* add trade direction to more logs
* add query filter to trade status title
* separate trade status for test env any-1m and any2-1h
* no tpsl for test any #1 containers
* differenciate between stochf and strochrsi in graphing
* fix stochrsi indexing and graphing
* add data 5m and 4h containers
* different channel for different data interval containers
* no longer need HOST env var for all containers
* add proper scheduling for get_data runs and healhcheck
* unique lock files for get_data containers
* add direction grouping for profitable view and use close_time for order
* move some test alerts to seperate channel
* increase test log verbosity
* add drawup/down debug logging
* allow open trades to be filtered
* correct path for get_bnb cron script
* combine active_trade/trade_status scripts
* add missing prod 1m containers

# 5.14
* Fix staging container names
* add 1m prod api strategies
* don't try to create close link for eng containers
* rename any prod to include 1h and matching DC name
* remove old prod containers from links
* remove unused prod config
* tweak prod to match 1h test env
* don't try to modify header line of trade list notification

# 5.13.1
* only add direction to name if it doesn't already have it
* replace more print statements with debug logging

# 5.13
* catch exceptions from cron scripts
* fix time in trade values for all envs
* increase time between trades test env
* display 1m graph for 1s strategy
* tweak 1h strategy
* use container name to get short-name
* fix open alert close link
* use correct trade direction for each open trade
* source container vars in cron
* fix internal trade link
* reduce size of trade list before notifying
* source vars from env file
* use shortname in trade status
* ensure we use right db for drawup/down
* replace print with logger statement
* get correct short name with direction for link
* add VPN_IP env var to cron containers
* add close link to trade status notifications
* move api functions to common lib
* ensure c9e names match dc names
* remove dupe code
* Bump werkzeug from 2.2.0 to 2.2.3 - security fix
* differentiate between buy/sell and open/close

# 5.12.1
* Match env at beginning of container name when alerting on exceptions
* Ensure we fetch more candles when timeframe is x seconds or minutes
* Add logwatch container to test env
* ensure we pop items from list, not tupple/string when printing current trades

# 5.12
* statefile for disabling audio alarms per env
* Add interval to TV link in trade status alerts
* Fix docker status alert script by matching container string

# 5.11
* run UI command in background and reutrn immediately
* tweak test env params
* separate redis functions into different dbs
* remove redis db from config and use add default
* remove delisted pairs
* fail gracefully when no candles for a pair
* remove test drain hours
* add 1h and 1m test envs

# 5.10.1
* Fix syntax error

# 5.10
* send trade messages to trade slack channels
* add router links to manual containers in all envs
* remove contents, not table when recreating usable pairs
* check environment before alerting on exception
* properly check that dframe is not None
* separate dupe pickle data code into function
* create new key if redis data doesn't exist (API containers)

# 5.9
* add long/short route for any2 test strategy
* add only row from loop and ensure it is appended correctly
* add latest redis data to data notification
* speed up initial run by reducing data klines
* combine calls to redis to further reduce run time for initial and loop
* Remove unused code from binance_common
* restore threading in get_dataframes for speed
* don't get initial data twice as it's overwritten by the same data
* merge data from all downloaded klines to ensure no missing data
* show start/end time of downloaded klines from openTime and closeTime

# 5.8.1
* Fix logtailer env name in prod
* Hide logtailer port in per

# 5.8
* Skip processing of dataframe if no new data
* Check interval needs to be low 60 seconds
* Increase waiting times between data prod runs for 1h
* Don't allow dupe close time values in instance df
* Overwrite kline data if data for incomplete candle already exists, otherwise append
* Get a few candles to ensure df isn't empty
* Use correct logwatch/logtailer names in all envs
* Install valid version of ccxt
* Correct selenium links
* Fix webserver healthchecks
* Fix data env nginx port assignment
* Add 2nd test envs for long/short any pairs
* Ensure all containers contain env in name
* Use large no of klines for redis cleanup and add logging

# 5.7
* increase 1m klines to allow for empty data
* increase number of max klines available and remove empty dfs
* use json to decode string instead of literal_eval
* run analyzer for 1h less often
* tweak data strategies and increase number of klines for accuracy
* tidy up bbperc code
* tweak stag bbperc short strategy
* remove depricated pairs
* correct bbperc  index when using live data
* bump binance version to use random api host
* cleanup all available redis keys/pairs
* add bbperc to seperate graph
* always check ISOLATED & CROSS pairs in data env
* show unmatched docker container in logwatch
* remove bbperc EMA
* use a single deploy log for each server
* tidy up docker compose yaml lint
* remove 5m and add 1h data bb env
* use new syntax after config reversion
* upgrade requests for openssl compatibility
* revert stag bbperc to previous settings
* don't use wrapper function for run tests
* reorganise tests for efficiency
* improve unittest lint
* don't delete test files on completion
* allow re-using downloaded test data to speed up jenkins run
* set default loan amount of zero before calculations

# 5.6.1
* Fix version conflicts
* Remove delisted pairs
* Get 2 dataframes for each run
* Fix rate indicator for data env
* Remove deprecated push code/config

# 5.6
* More test strategies
* Improved check syntax to allow for additional historical data
* Don't refetch the same candles on subsequent prod runs/checks
* Ensure candle data stored in instance doesn't exceed max candles
* Cleanup logging complexity for trade status

# 5.5.2
* When shorting, buy back only the amount originally sold
* Add pair name for skipped trades during drain

# 5.5.1
* Fix prod indicator name

# 5.5
* reduce verbosity of NaN/None Engine data
* display time from candle in notification
* use ask/bid price when not using test data
* notify when starting gc build
* seperate out 2 stag envs
* only check for cross/isolated pairs once
* cleanup extracting data from exchange
* enure we only get commisssion in prod with non-test trades
* ensure we declare trade_result in test mode
* use updated prod strategy

# 5.4
* add api containers for bb eng strategies
* Improve trade output logging
* Add second bbperc stag strategy
* add any to bb short api name
* don't refetch redis data for current_price
* Use actual port for webserver
* Remove current_price from each redis key
* Trial changes to 1m/5m data containers
* fix string action in order module
* enable delay between data notifications
* always use last candle for analysis and ohlc data

# 5.3
* fix port allocations and conflicts for web
* fix get_var db function
* get db variable contents
* allow override max trade value to be fetched from db vars table
* fix log showing wrong direction
* increase divisor for other prod cross strategies
* rule under list of open trades for visibility
* don't re-raise exception when unable to get trade_id
* don't create graphs in prod
* use current_price from OHLC data
* ensure we have an amount to use if no loan available
* alert when not enough bnb in x-margin (cron)

# 5.2
* Allow getting trades with or without direction in scope
* Format current USD profit in hourly notification
* Fix number of args returned from mysql method
* Support using non-standard port for api request forwarding
* Fix api backend for non-test envs
* Remove test flag for prod env

# 5.1
* Use unique exposed ports for each env
* Ensure close rules never match when we are using TP/SL
* No longer require checking interval in open trades - use name
* Decom unused api-web containers everywhere
* Reduce prod max trade value
* Unique filename for check-data lockfile per env
* Check we have available balance/loan before attempting trade open
* Mount ipython volume for history preservation
* Rename containers in prod
* Missing pair raising exception in prod
* Fix Null string evaluation in redis

# 5.0.1
* Fix typo in prod DC config
* Wait for data collection to finish in backend

# 5.0
* Various new db views to assist with finding profitable pairs
* Add bbperc and bbperc with EMA indicators
* bbperc strategy with supertrend for all envs
* Strip whitespace from pair before creating graph links
* Continue with trade if unable to borrow
* Allow restricting trade to a max amount (loan + available)
* Better unified logging when opening/closing trades
* Add numerical trade action to trade request
* Methods to calculate total trade amount with max var
* Remove pickle and zlib compression of ohlc data
* Fix redis data to be jsonifed for new redis version
* Forward API requests to different environments
* Redis queue for incoming API requests
* Don't save auto_inc value in db schema
* Wait for initial data collection before analysing data
* Cleanup of docker entryfiles
* Various tests in stag and test envs
* More data in hourly profit notifications
* Fetch table of good pairs from different DBs
* Cleanup old redis entries, and only keep last 250 items for each pair

# 4.8
* Data migration between stag and test envs
* Fixes for assocs tests not running on all envs
* Log date and pair when missing data in redis
* Allow backend to run withing fetching data
* Adding supertrend to data env
* Use epoch from redis candle data
* Debug cleanups
* Improve logging for missing data
* Show pairs that were skipped when attempting trade
* Use epoch of previous candle, not current time
* Fix port conflicts when running multiple envs on single host
* Allow backend to run without fetching data (use redis)
* Update jenkins slave docker image
* Run intermittent checks more frequently
* Install ipython to manual containers on startup
* Allow data containers to forward trade requests to other envs
* Close trade after time-out if over perc profit threshold and check intermittently
* Don't download GBP/USD rates when using test data
* Allow using common name for short/long containers to combine max_trades
* More logging when starting/finishing intermittent checks
* Tweak data and corresponding test strategy
* Add direction when fetching open_trade information
* Add open/close times to trade notifications
* Hack for 15-line slack limitation when showing open trades
* Add number of trades to hourly profit notifications

# 4.7
* Fixes to data dashboard
* Fixes to redis writing
* Increase graph logging
* Fixes to logtailer web path
* Fixes to short borrowing
* Fixes to triggered data alerts
* New pairs for data
* Don't re-request current price when data is available in candle
* Removal of retired pairs
* Fix supertrend indicator
* Various bb and bbperc test strategies with Supertrend
* Don't use lock file while waiting for data collection
* Add tradingview interval translation dict
* Cleanup data env
* Don't update draw up/down when not in a trade
* Updated docs
* New db views for perc and profitable perc by stategy/name
* Remove pairs which don't have a corresponding USDT trading pair
* Better logging when data missing from redis
* Increase db field size for currencies
* Fixes to testing quote amounts

# 4.6
* Get details of all isolated margin pairs
* Script to transfer funds to/from isolated and spot
* Allow partial last candle in data env to catch signals earlier
* Reduce number of initial candles in data env
* Cleanup and reduce logging
* Consolidate redis data into pair:interval keys
* Remove duplication of date and current price in redis
* Don't stop deployment if no fe or be containers already running
* Deprecate expiration of redis rows due to consolidation of data
* Add new redis cleanup script for data expiry for use in cron
* Remove old unit redis unit tests covered by other tests
* New redis docs
* Fix data web port and add filesystem/router containers
* Check borrowable amount is less than what we intend to borrow
* Fix new ETHW coin errors
* Don't use updated version of pyopenssl
* Remove recently retired trading pairs
* Add current price and UTC time to data trade notifications
* Create graphs for all data timeframes
* Check data results more frequently
* Keep graphs for up to 2 days
* Don't set indicator value to zero if no value
* Don't trigger the same trade notifications more than once per hour
* Restore low/high RSI data containers
* Ensure data healthchecks are not shared and are stored locally
* Increase data logging verbosity to debug
* Create graphs in unittest runs

# 4.5
* Add more pairs for analysis in data env
* Allow specifying binance api endpoint from config
* Cleanup docker after jenkins success/falure to conserve networks
* Updated version of jenkins slave image
* Fix setuptools pip in gc image
* Allow infinite isolated trades
* Enable intermittent checks in all prod trade containers
* Temporarily enable binance debug mode to get mock data
* Fix cron test image using mysql image causing intermittent failures

# 4.4
* Cleanup isolated alerts - don't print if balance < 0
* Allow manual overriding TP & SL for existing trades
* Various fixes for streamlining and speeding up jenkins unittests
* Docs for running local tests
* Fix for calculating actual commission used from exchange data
* Remove a further 1% from amount of margin to open trade with before applying step-precision

# 4.3
* Fix deployment to kill all be/fe containers for starting new ones
* Get converted USD commission from dict before storing
* don't use everything in isolated account
* Don't try to get commission in non-prod envs
* Syntax and var fixes
* Fix for int too large for db
* Better alerting for invalid pair from API
* Add 15m trend to data env
* Allow specifying TP/SL through API
* Speed up jenkins test/build/docker push by combining containers
* Fixes to docker compose files
* Don't fail deployment if no be/fe containers to kill
* Use commit hash when running unit tests and creating images
* Get free amount from exchange, not net from DB


# 4.2
* Cleanup old strategies/containers
* Use correct strategy naming convention
* Fix loan repayment not correctly truncating amount
* Assume zero balance if key not found in margin short
* Stop prod automatic debt repayments
* Collect and store order id for each trade open/close in production
* General cleanup

# 4.1.1
* Fix margin long open

# 4.1
* Order module cleanup and comments
* Fix short to use base amt in trade, not quote
* Fix isolated to use entire amount with only 1 concurrent trade
* Debug alert for loan repayment errors
* More logging when trade open fails

# 4.0
* Upgrade all envs to docker-compose 2.x
* Hack to use 1m timeframe from < 1m specified due to binance limitations
* Helper function for converting epoch to string/time object
* Print start date of downloaded test data
* Only calculate profit when trade is closed
* Return False if trade operation has failed and check when returned
* Don't truncate DB amounts when calculating percentage
* Add more commands to GC commands UI
* Only send a single trade to trades module for open/close operation
* Script to populate missing DB rates
* Script to open graphs in browser
* Add 12h, 1h, and 15m to date env
* Remove low volume 5m pairs from data env
* Unit tests for borrow method
* More run unit tests for cross/isoolated long/short
* Cleanup return statements
* Longer varchar in DB for new naming scheme
* Add new accounts query to DB as view
* Deprecate multiplier config item and use divisor
* For Cross/Isolated margin use borrowable amount and available amount
* Deprecate amount_to_use method and add functionality to other methods
* Don't use free amount when calculating amount to borrow
* Separate out prod and per cron tables

# 3.33
* Changes to test trades
* Method to manually restore TP/SL in redis
* Get asset information in isolated margin account
* Increase thresholds for opportunity containers for less alerts
* Ensure all data containers have matching indicators
* Remove unused stochrsi indicator from opportunities
* Remove high-rsi containers, keeping very-high rsi
* Commission var/function held in DB from variables table
* Use commission var in DB views when creating open_trades table
* Fix short trade notification amounts
* Fix ID from trades table not auto incrementing in some envs
* Return ID of inserted or updated trade
* Ensure we check all accounts for a balance so we have a consistent number of rows returned
* Always check we have an open trade to close before attempting any calculations with NULL values

# 3.32
* Add repay_depts command to commands UI
* Ignore empty spot balance when fetching quote balances
* Add stag strategies
* Use DB commission table/function in profit view
* Display pair for each non-empty isolated balance
* Don't check BNB in spot account for cross account

# 3.31
* Fix error when trying to close a trade which isn't open
* Allow Jenkins to pick up screenshot from selenium tests
* Trim down personal environment
* Remove now redundant GC_PORT var and hard code value
* Add 4h stag env for further testing
* Separate route for long/short testing env
* Check for profit in last hour before sending out notif
* Fix db test running out of sequence
* Use db functions to create derived profit/perc data
* Add single commission var in db table/function
* Fix DB method not returning same sized tuple when no data

# 3.30.1
* Fix trade closes to use name and pair for fetching profit
* Move deployment state file to /var/local persistent director

# 3.30
* Fix for test balances incrementally increasing
* UID fox for db trades table inserts/updates
* Fix for debts not periodically being paid off
* Use re-calculated amount when closing short trades
* Fix Short trade amount notifications giving false positives

# 3.29
* Add full list of debts and free assets in X-margin notifications
* Add total debt in X-margin
* Add BCHUSDT to prod trades
* Cleanup prod environment container names

# 3.28
* Add selenium tests
* Update Jenkins image to include python selenium deps
* Update Flask-Login to use updated version of Werkzeug
* Add dep links for proxy/filesystem containers

# 3.27.1
* Fix syntax error

# 3.27
* Move drain files to persistent dir
* Retry Binance requests which time out
* Add direction/strategy name to db view grouping
* Recreate some DB views
* Add net values to hourly profit notifications and set title
* Disable audio alert where var is undefined
* Hack to support 1s intervals although binance doesn't support below 1m

# 3.26.1
* Fix to not upgrade werkzeug to latest

# 3.26
* New INW strategy for test env
* Config fixes
* Add Filesystem and proxy containers to all environments

# 3.25
* Fix balance graphs
* Website formatting for mobile screens
* Add path to repay cron script
* Fix DB percent function for negative values
* Tweak config for prod strategy
* Ensure non-prod containers use same config for short vs long

# 3.24
* New keys for data env
* Fix Setuptools in manual containers
* Env changes in test env for short-term tests
* Move TSI to bottom graph pane
* Make volume graph opt-in
* Disable trade alerts for some environments
* Add healthchecks for alert container
* Allow container to be disabled
* New prod containers for stochRSI strategy
* Cleanout old strategies from all envs
* Set timezone to UTC during bootstrap
* Fix DB schema tool not preserving views
* Recreate DB views
* Add net values to DB views
* Allow specifying table/view name when creating drawdown/drawup charts
* Mysql procedure to deduct percentage (commission)

# 3.23
* Allow running of balance cron commands from UI
* Use open_time for graphs to match tradingview
* Display versions of each environment and add to UI
* Password protect all Flask API pages
* Use flask for traversing data dir
* Reduce number of redis entries in data env
* Cleanup outdated redis entries periodically
* Fix vagrant dev env ntp sync
* Add proxy container to allow access to internet containers
* Show UI pages in iframe
* Separate out prod/per environments onto different servers

# 3.22
* Security improvements
* Port changes to avoid conflicts
* Disable alerts for stag environment
* Don't wipe data env before starting up
* Cleanup of graphs
* Cleanup of pairs for lower timeframes
* Add StochRSI to 5m data strategy
* Move deployment info to /var/run

# 3.21
* Balance slack notifications have title of script
* Log details of deployment to file for later collection
* Downgrade some INFO logs in data info to DEBUG
* Allow TSL staging to go to 0.4 before closing position
* Drain file, for immediately stopping all new trades
* Allow data analysis to happen immediately after collection

# 3.20
* Avoid exception loop by removing redis entries before trade closes
* Display pair from SL/TP exception and re-raise
* Fix prod containers referencing per deps
* Add Build information to docker images as env vars

# 3.19
* Add C9e environment and install ipython to manual containers
* Add staging containers with trailing stop loss
* Reformat profit notif
* Remove SL/TP from redis when stopped out or taken profit
* Fix ordering of trades in stus notifications
* Fix calculations of TP and SL

# 3.18.1
* Fix usd quote gving base figure
* Fix Formatting of usd_quote and avail BNB

# 3.18
* Calculate net perc and add to DB/trade alerts
* New db schema for modified view
* Only try to borrow funds if we have sufficient available
* Fix for LBUSD
* Support BUSD in sport and margin
* Fix for data graphs not being created
* Add 1h data graphs to cron
* Container for running manual commands with no alerts/journald logging
* Add no "any" strategies with 2% and 5% TP for per and prod envs
* Cmd line script to get GBP & USD exchange rates for a given quote symbol
* Fix broken authentication for /action api route
* Include current borrowed amount(s) before calculating borrow amount for next trade
* Cron script to repay as many debts as possible - hourly
* Minor code cleanup
* Enforce specific version of yq on all environments
* Tweak prod env INW trade settings

# 3.17.1
* Fix usd_amount calculation

# 3.17
* Only repay what we actually have when closing margin trades
* Try to repay all debts periodcally
* Wait a couple more seconds before marking docker-compose redis/mysql unhealthy

# 3.16
* Add drain hours to production
* Fix Sell-now link using wrong port for production
* When calculating amount to borrow, also use amount already borrowed in the same short/long
  strategy

# 3.15
* Fix get_borrowed function to not exit look pre-maturely
* Extra logging for short borrowing
* red alert api to listen on host port for monitoring
* Fix for LDBUSD
* Allow for zero balance on spot and phemex
* Tweak testing balances
* Remove delisted testing pairs

# 3.14
* Change of creds
* Fix red alert container not starting
* Use only a single trend indicator for api trades

# 3.13
* add IWN containers for prod env
* add 2nd trend (1h) to INW - all envs
* Fix table/view names
* Add authentication to flask API views
* Web UI improvements
* Consolidate entryfile scripts
* different entrypoint actions for web-api and webserver containers
* Increase and balance out test balances

# 3.12.1
* Only 1 log tailer per server linked to all environments with a UI
* Reduce INFO logging
* Better log streaming

# 3.12
* Cleanup docker-compose files
* Fix short notifications in data env
* Tail logs in Web UI
* Remove old logging
* Fix alert sound
* Add average profit to hourly notifications
* Add more mysql unit tests
* Remove all python relative imports
* Align trades table field type

# 3.11.1
* Fix cron entry for hourly profit
* Add HOST_IP var to per containers
* fix close-now link on trade-open notifications
* Minor syntax fix

# 3.11
* Add API route checks
* Custom emojis for opportunities channel notifications
* Cleanup strategy names

# 3.10.1
* Fixes to hourly profit cron and query
* Add Day-of-week to db views

# 3.10
* Upgrade mysql client to match server
* Cleanup mysql config
* Speed up pair tests and remove old pairs
* add static port mapping for redis test env
* Add drawup/drawdown to API trades
* Use current price for draw up/down if within current candle otherwise use high/low
* Add 5m analysis to data env
* Don't prune docker after deployment as it affects other environments being deployed
* Fix SQL container in local (unit) environment
* Fix bug with hourly profit notifications

# 3.9.1
* Fix for DB view referencing non-existent views
* Updated DB schema

# 3.9
* Upgrade Mariadb to 10.8
* Cleanup data environment container names
* Add new views for profit over different timeframes
* Cleanup view names
* Cleanup for views displaying null entries
* add waves pairs to staging/data
* Fix for hourly profit cron

# 3.8
* Link to override skipped api trade
* Log skipped details
* Get hourly profit and notify slack after each hour
* Fixes for percentage calculation and formatting
* Cleanup of old trading pairs
* New view to get profit aggregated profit per hour for all available days
* Change slack title if trade action was initiated manually
* New INW trading pairs
* Use long-short combined strategy for TV API link
* Various code cleanups
* New test environment
* Time period for drain-mode
* Set strategic downtime/drain for per env

# 3.7.1
* Don't check TL/SL for all api containers, unless enabled
* hourly cron to run just after the hour
* minor code cleanup and exception handling
* Only get profit in prod/per/stag environments

# 3.7
* Fixes for collecting API commission data
* Rename data env
* Fix Null values in DB
* Restructure data c9e envs
* Add data containers for determining trend
* Allow all envs to determine trend via API alls
* Repurpose "any" envs for INW API strategy
* Prod envs for INW API strategies
* Keep images on test failure for debugging
* Add debugging router for API trend
* All pairs in slack notifications are now TV links
* Create graphs for data env pairs using cron
* Allow manual trades to go through even if against current trend
* Fix NET perc/profit in slack notifications
* Add hourly profit view
* Use cron to notify of profit earned in previous hour
* Remove old DB tables and views
* add hostname arg to db schema script

# 3.6.1
* Fix comparison type
* Fix API config location

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


