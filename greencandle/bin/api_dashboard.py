#!/usr/bin/env python
#pylint:disable=no-member,consider-using-with,too-many-locals,global-statement,too-few-public-methods,assigning-non-slot,no-name-in-module,broad-exception-caught,expression-not-assigned

"""
Flask module for manipulating API trades and displaying relevent graphs
"""
import re
import ast
import os
import json
import time
import subprocess
import logging
from time import gmtime, strftime
from collections import defaultdict, Counter
from datetime import timedelta, datetime
from str2bool import str2bool
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request, Response, redirect, url_for, session, g
from flask_login import LoginManager, login_required, current_user
from setproctitle import setproctitle
from send_nsca3 import send_nsca
from greencandle.lib.redis_conn import Redis
from greencandle.lib.auth import binance_auth
from greencandle.lib.mysql import Mysql
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.binance_accounts import base2quote, get_cross_margin_level
from greencandle.lib.common import (arg_decorator, divide_chunks, get_be_services, list_to_dict,
                                    perc_diff, get_tv_link, get_trade_link, format_usd,
                                    AttributeDict, price2float)
from greencandle.lib import config
from greencandle.lib.web import PrefixMiddleware, push_prom_data, decorator_timer
from greencandle.lib.balance_common import get_quote
from greencandle.lib.balance import Balance
from greencandle.lib.flask_auth import load_user, login as loginx, logout as logoutx

config.create_config()
APP = Flask(__name__, template_folder="/var/www/html", static_url_path='/',
            static_folder='/var/www/html')
APP.wsgi_app = PrefixMiddleware(APP.wsgi_app, prefix='/dash')

LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.init_app(APP)
LOGIN_MANAGER.login_view = "login"
APP.config['SECRET_KEY'] = os.environ['SECRET_KEY'] if 'SECRET_KEY' in os.environ else \
        os.urandom(12).hex()
LOAD_USER = LOGIN_MANAGER.user_loader(load_user)
LOGIN = APP.route("/login", methods=["GET", "POST"])(loginx)
LOGIN = APP.route("/logout", methods=["GET", "POST"])(logoutx)

VALUES = defaultdict(dict)
BALANCE = []
LIVE = []
STATUS_DATA = []
DOUBLERSI={}
AGG_DATA = []
DATA = AttributeDict()

SCRIPTS = ["write_balance", "get_quote_balance", "repay_debts", "get_risk", "get_trade_status",
           "get_hour_profit", "repay_debts", "balance_graph", "test_close"]
ARG_SCRIPTS = {"close_all": ['name_filter', 'threshold', 'pair_filter']}

@decorator_timer
def get_doublersi():
    """
    RSI strategy data using 2 timeframes
    """
    global DOUBLERSI
    sorted_dict = {}
    config.create_config()
    redis = Redis()
    now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    for pair in config.main.pairs.split():
        try:
            item = redis.get_intervals(pair, '1d')[-1]
            x = json.loads(redis.get_item(f'{pair}:1d', item).decode())

            item2 = redis.get_intervals(pair, '1h')[-1]
            x2 = json.loads(redis.get_item(f'{pair}:1h', item2).decode())

            if x['RSI_7'] > 60 and x2['RSI_7'] < 40 :
                direction='long'

            elif x['RSI_7'] < 40 and x2['RSI_7'] > 60:
                direction='short'
            else:
                continue

            DOUBLERSI[pair] = {'day': x['RSI_7'],
                             'hour': x2['RSI_7'],
                             'time': now,
                             'direction': direction}
        except Exception as e:
            print("bad %s",e, pair)

    sort = sorted(DOUBLERSI,key=lambda x:DOUBLERSI[x]['time'])
    for key in sort:
        sorted_dict[key] = DOUBLERSI[key]

    DOUBLERSI = dict(list(sorted_dict.items())[:100])

def get_doublersi_list():
    """
    Get latest double rsi data and re-format for spreadsheet
    """
    x = []

    columns = ['pair', 'direction', 'day', 'hour', 'time']
    index_map = {v: i for i, v in enumerate(columns)}
    for key_pair, di in DOUBLERSI.items():
        di['pair'] = get_tv_link(key_pair, '1h', anchor=True)

        x.append(dict(sorted(di.items(), key=lambda pair: index_map[pair[0]])))
    return x

@decorator_timer
def get_pairs(env=config.main.base_env):
    """
    get details from docker_compose, configstore, and router config
    output in reversed JSON format

    Usage: api_dashboard
    """
    docker_compose = open(f"/srv/greencandle/install/docker-compose_{env}.yml", "r",
                          encoding="utf-8")
    pairs_dict = {}
    names = {}
    length = defaultdict(int)
    pattern = "CONFIG_ENV"
    for line in docker_compose:
        if re.search(pattern, line.strip()) and not line.strip().endswith(('prod', 'api', 'cron')):
            env = line.split('=')[1].strip()
            command = f'configstore package get --basedir /srv/greencandle/config {env} pairs'
            result = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            pairs = result.stdout.read().split()
            command = f'configstore package get --basedir /srv/greencandle/config {env} name'
            result = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            name = result.stdout.read().split()
            pairs_dict[env] = [pair.decode('utf-8') for pair in pairs]
            length[env] += 1
            names[env] = name[0].decode('utf-8')
    for key, val in pairs_dict.items():
        length[key] = len(val)
    return pairs_dict, dict(length), names

@APP.before_request
def before_request():
    """
    Perserve session
    """
    session.permanent = True
    APP.permanent_session_lifetime = timedelta(weeks=1)
    session.modified = True
    g.user = current_user

@APP.route('/healthcheck', methods=["GET"])
@login_required
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

@APP.route('/commands', methods=["GET"])
@login_required
def commands():
    """Run commands locally"""
    return render_template('commands.html', scripts=SCRIPTS, arg_scripts=ARG_SCRIPTS, alert=None)

@APP.route('/internal', methods=["GET"])
@login_required
def interal():
    """Load internal page"""
    page = "http://" + request.args.get('page')
    resp = requests.get(page, timeout=20)
    if page.endswith('png'):
        filename = os.path.split(page)[-1]
        return render_template('image.html', filename=filename)
    return render_template('internal.html', page=resp.content.decode())

@APP.route('/iframe', methods=["GET"])
@login_required
def example():
    """Load page in an iframe"""
    page = request.args.get('page')
    return render_template('iframe.html', page=page)

@APP.route('/run', methods=["POST"])
@login_required
def run():
    """
    Run command from web
    """
    command = request.args.get('command')
    args = request.form.to_dict(flat=False)
    args.popitem() #remove submit button
    output = None

    if command.strip() in SCRIPTS:
        output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elif any(command.strip() in sublist for sublist in ARG_SCRIPTS):
        args = {key: value[0] for key, value in args.items() if value[0].strip() !=""}
        for key, value in args.items():
            # add args to command
            command += f' --{key} {value}'
        output = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    alert = process_subp_output(output) if output else "No output"
    return render_template('commands.html', scripts=SCRIPTS, arg_scripts=ARG_SCRIPTS,
                           alert=f'{command.strip()}: {alert}')

def process_subp_output(output):
    """
    Concat stdout/stderr from subprocess buffer and remove line breaks
    """

    return output.stdout.read().decode().replace('\n', ' ').replace('\r','') + \
           output.stderr.read().decode().replace('\n', ' ').replace('\r','')

@APP.route('/charts', methods=["GET"])
@login_required
def charts():
    """Charts for given strategy/config_env"""
    config_env = request.args.get('config_env')
    groups = list(divide_chunks(get_pairs()[0][config_env], 2))

    return render_template('charts.html', groups=groups)

@APP.route("/xredis", methods=['POST'])
@login_required
def xredis():
    """
    delete key from redis
    """
    key = request.args.get('key')
    redis_db = int(request.args.get('db'))
    redis = Redis(db=redis_db)
    redis.conn.delete(key)

    return redirect(url_for('extras'))

@APP.route("/extras", methods=['POST', 'GET'])
@login_required
def extras():
    """
    Form for entring new open|close trade rules
    and table for displaying current rules stored in redis
    """

    redis = Redis(db=12)  # current_rules
    redis7 = Redis(db=7) # saved_rules
    redis11 = Redis(db=11) # triggered_rules
    data = defaultdict(list)
    rules = []
    keys = redis.conn.keys()
    keys7 = redis7.conn.keys()
    keys11 = redis11.conn.keys()
    time_format = "%Y-%m-%d %H:%M:%S"
    with open('/etc/router_config.json', 'r', encoding="utf-8") as json_file:
        router_config = json.load(json_file)
    routes = [x for x in router_config.keys() if 'extra' in x]

    for key in keys7:
        rules.append(ast.literal_eval(redis7.conn.get(key).decode()))
        delete_button = (f'<form method=post action=/dash/xredis?key={key.decode()}&db=7><input '
                          'type=submit name=save value=delete></form>')
        rules[-1].append(delete_button)

    for key in keys:
        current = AttributeDict(json.loads(redis.conn.get(key).decode()))
        pair = current['pair']
        interval=current['interval']
        current['pair'] = get_tv_link(pair, interval, anchor=True)

        delete_button = (f'<form method=post action=/dash/xredis?key={key.decode()}&db=12><input '
                          'type=submit name=save value=delete></form>')
        readd_button = (f'<button onclick="javascript:populate(\'{pair}\', \'{interval}\', '
                        f'\'{current.action}\', \'{current.usd}\', \'{current.tp}\', '
                        f'\'{current.sl}\', \'{current.rule}\', \'{current.rule2}\', '
                        f'\'{current.forward_to}\')">re_addd</button>')

        current.update({'re_add': readd_button})
        current.update({'delete': delete_button})
        add_time = datetime.fromtimestamp(int(key)).strftime(time_format)
        current.update({'add_time': add_time})
        data['current'].append(current)

    for key in keys11:
        processed = AttributeDict(json.loads(redis11.conn.get(key).decode()))
        pair = processed['pair']
        interval = processed['interval']
        processed['pair'] = get_tv_link(pair, interval, anchor=True)

        delete_button = (f'<form method=post action=/dash/xredis?key={key.decode()}&db=11><input '
                          'type=submit name=save value=delete></form>')

        readd_button = (f'<button onclick="javascript:populate(\'{pair}\', \'{interval}\', '
                        f'\'{processed.action}\', \'{processed.usd}\', \'{processed.tp}\', '
                        f'\'{processed.sl}\', \'{processed.rule}\', '
                        f'\'{processed.forward_to}\')">re_addd</button>')
        processed.update({'re_add': readd_button})
        processed.update({'delete': delete_button})
        add_time = datetime.fromtimestamp(int(key)).strftime(time_format)
        processed.update({'add_time': add_time})
        data['processed'].append(processed)

    if request.method == 'POST':
        args = request.form.to_dict(flat=False)
        args = {key: value[0] for key, value in args.items() if value[0].strip() !=""}
        args.popitem() #remove submit button
        args = defaultdict(str, args)  # enforce field with empty string if not present

        fields = ['pair', 'interval', 'action', 'usd', 'tp', 'sl', 'rule', 'rule2', 'forward_to']
        data_str = json.dumps({x:args[x] for x in fields})

        redis.conn.set(f"{str(int(time.time()))}", data_str)
        time.sleep(2)
        return redirect(url_for('extras'))
    return render_template('extras.html', data=data, routes=routes, rules=rules)

@APP.route("/action", methods=['POST', 'GET'])
@login_required
def action():
    """
    get open/close request
    """

    # get integer value of action
    # keep open the same as we don't know direction
    int_action = {"open": "open",
                  "close": 0,
                  "short": -1,
                  "long": 1,
                  }

    pair = request.args.get('pair')
    strategy = request.args.get('strategy')
    trade_action = int_action[request.args.get('action')]
    close = request.args.get('close')
    take = request.args.get('tp') if 'tp' in request.args else None
    stop = request.args.get('sl') if 'sl' in request.args else None
    usd = request.args.get('usd') if 'usd' in request.args else None

    send_trade(pair, strategy, trade_action, take=take, stop=stop, usd=usd)
    if close:
        return '<button type="button" onclick="window.close()">Close Tab</button>'
    return redirect(url_for('trade'))

@decorator_timer
def send_trade(pair, strategy, trade_action, take=None, stop=None, usd=None):
    """
    Create OPEN/CLOSE post request and send to API router
    """
    payload = {"pair": pair,
               "text": f"Manual {trade_action} action from API",
               "action": trade_action,
               "strategy": strategy,
               "manual": True,
               "tp": take,
               "sl": stop,
               "usd": usd}

    api_token = config.web.api_token
    url = f"http://router:1080/{api_token}"
    try:
        requests.post(url, json=payload, timeout=1)
    except Exception:
        pass

@APP.route('/trade', methods=["GET"])
@login_required
def trade():
    """
    open/close actions for API trades
    """
    pairs, _, names = get_pairs()

    rev_names = {v: k for k, v in names.items()}
    with open('/etc/router_config.json', 'r', encoding="utf-8") as json_file:
        router_config = json.load(json_file)

    env = config.main.base_env
    links_list = get_be_services(env)
    links_dict = list_to_dict(links_list, reverse=True, str_filter='-be-api-any')

    my_dic = defaultdict(set)
    for strat, short_name in router_config.items():
        for item in short_name:
            name = item.split(':')[0]

            if not name in ['alert', 'forward']:
                try:
                    container = links_dict[name]
                except KeyError:
                    continue
            else:
                continue

            try:
                config_env = rev_names[container]
            except KeyError:
                # remove -long/-short from container names
                # this is to support long/short containers
                # with the same name
                container = re.sub(r'-\w+$', '', container)
                config_env = rev_names[container]

            xxx = pairs[config_env]
            my_dic[strat] |= set(xxx)

    return render_template('action.html', my_dic=my_dic)

def get_value(item, pair, name, direction):
    """
    try to get value from global dict if exists
    otherwise return -1
    """
    try:
        return VALUES[item][f"{pair}:{name}:{direction}"]
    except KeyError:
        return -1

@decorator_timer
def get_agg():
    """
    collate aggregate data from redis
    """
    global AGG_DATA
    all_data = []
    redis = Redis(db=3)
    keys = redis.conn.keys()
    columns = ['distance_200', 'atr_avg_dist', 'atr_4', 'cci', 'candle_size', 'avg_candles',
               'sum_candles', 'rsi', 'macd_diff', 'middle_200', 'bb_size', 'stoch_flat', 'num',
               'bb_size', 'bbperc_diff', 'bbperc', 'macd_xover', 'atrp', 'empty_count',
               'stx_diff', 'date']
    for key in keys:
        cur_data = redis.conn.hgetall(key)
        decoded = {k.decode():v.decode() for k,v in cur_data.items()}
        pair, interval = key.decode().split(':')
        sort_data = dict(sorted((x for x in decoded.items() if x[0] in columns),
                                key=lambda pair: columns.index(pair[0])))
        current_row = {}
        current_row.update({'pair': get_tv_link(pair, interval, anchor=True),
                            'interval':interval})
        for function, value in sort_data.items():
            current_value = '' if 'None' in value else value
            current_row.update({function:current_value})
        all_data.append(current_row)
    AGG_DATA = all_data

def get_trend_colour(value, direction):
    """
    get HTML red/green colour based on trend and direction
    """
    if direction == 'long':
        colour = 'green' if 'SELL' not in value else 'red'
    else:
        colour = 'green' if 'BUY' not in value else 'red'

    return f'<p style="font-weight:bold;color:{colour}">{value}</p>'

def get_bool_colour(value):
    """
    get HTML red/green colour based on boolean result
    """
    colour = 'green' if value else 'red'
    return f'<p style="font-weight:bold;color:{colour}">{value}</p>'


@decorator_timer
def get_live():
    """
    Get live open trade details
    """
    global LIVE, STATUS_DATA

    if config.main.base_env.strip() == 'data':
        return None

    all_data = []
    status_data = []
    mt5 = 0
    mt10 = 0

    dbase = Mysql()
    stream_req = requests.get("http://stream/5m/all", timeout=10)
    prices = stream_req.json()

    services = list_to_dict(get_be_services(config.main.base_env),
                            reverse=False, str_filter='-be-')
    raw = dbase.get_open_trades()
    commission = float(dbase.get_complete_commission())
    net_profitable = 0
    for open_time, interval, pair, name, open_price, direction, quote_in in raw:
        current_quote = get_quote(pair)
        current_price = prices['recent'][pair]['close']
        perc = perc_diff(open_price, current_price)
        perc = -perc if direction == 'short' else perc
        net_perc = perc - commission
        if net_perc > 0:
            net_profitable += 1

        if 5 < float(net_perc) < 10:
            mt5 += 1
        if float(net_perc) > 10:
            mt10 += 1

        trade_direction = f"{name}-{direction}" if \
                not (name.endswith('long') or name.endswith('short')) else name

        short_name = services[trade_direction]
        close_link = get_trade_link(pair, short_name, 'close', 'close_now',
                                    anchor=True, short_url=True, base_env=config.main.base_env)
        take = get_value('take', pair, name, direction)
        stop = get_value('stop', pair, name, direction)
        dist_to_take = round(take - net_perc, 2)
        dist_to_stop = round(stop - net_perc, 2)
        stochrsi = DATA[f'tf_{interval}'][pair].res[0]['STOCHRSI_14'][0]
        stochrsi_last = DATA[f'tf_{interval}'][pair].res[1]['STOCHRSI_14'][0]
        rsi7 = DATA[f'tf_{interval}'][pair].res[0]['RSI_7']
        rsi7_last = DATA[f'tf_{interval}'][pair].res[1]['RSI_7']
        ema150 = DATA[f'tf_{interval}'][pair].res[0]['EMA_150']
        ha = DATA[f'tf_{interval}'][pair].res[0]['HA_close']
        ha_last = DATA[f'tf_{interval}'][pair].res[1]['HA_close']

        rsi_up = rsi7 > rsi7_last if direction == 'long' else rsi7 < rsi7_last
        stoch_up = stochrsi > stochrsi_last if direction == 'long' else stochrsi < stochrsi_last
        ha_up = ha > ha_last if direction == 'long' else ha < ha_last
        if direction == 'long':
            bb_sell = float(current_price) > DATA[f'tf_{interval}'][pair].res[0]['bb_30'][0]
            ema_trend = float(current_price) > ema150
            rsi_sell = rsi7 > 70
            stoch_sell = stochrsi > 95
        else:
            bb_sell = float(current_price) < DATA[f'tf_{interval}'][pair].res[0]['bb_30'][2]
            ema_trend = float(current_price) < ema150
            rsi_sell = rsi7 < 30
            stoch_sell = stochrsi < 5

        time_in_trade = str(datetime.now().replace(microsecond=0) -
                            datetime.strptime(str(open_time), '%Y-%m-%d %H:%M:%S'))
        tv_trend = get_trend_colour(DATA[f'tf_{interval}'][pair]['sent'][0], direction)

        drawup = get_value('drawup', pair, name, direction)
        drawdown = get_value('drawdown', pair, name, direction)
        usd_in = quote_in if 'USD' in current_quote else base2quote(quote_in, current_quote+'USDT')
        usd_net_value = (float(usd_in)/100)*net_perc

        status_data.append({"pair": get_tv_link(pair, interval, anchor=True),
                            "interval": interval,
                            "time_in_trade": time_in_trade,
                            "xnet_perc": f'{round(net_perc,4)}',
                            "tv_trend": tv_trend,
                            "ema_trend": get_bool_colour(ema_trend),
                            "rsi_sell": get_bool_colour(rsi_sell),
                            "bb_sell": get_bool_colour(bb_sell),
                            "stoch_sell": get_bool_colour(stoch_sell),
                            "rsi_up": get_bool_colour(rsi_up),
                            "stoch_up": get_bool_colour(stoch_up),
                            "ha_up": get_bool_colour(ha_up),
                            "dist_to_take": dist_to_take,
                            "dist_to_stop": dist_to_stop,
                            "close": close_link,
                            "tp/sl": f"{take:.2f}/{stop:.2f}",
                            "du/dd": f"{round(drawup,2)}/{round(drawdown,2)}",
                            })

        all_data.append({"pair": get_tv_link(pair, interval, anchor=True),
                         "interval": interval,
                         "open_time": open_time,
                         "name": short_name,
                         "perc": f'{round(perc,4)}',
                         "net_perc": f'{round(net_perc,4)}',
                         "close": close_link,
                         "open_price": open_price,
                         "current_price": current_price,
                         "tp/sl": f"{take:.2f}/{stop:.2f}",
                         "du/dd": f"{round(drawup,2)}/{round(drawdown,2)}",
                         "quote_in": quote_in,
                         "usd_in": format_usd(usd_in),
                         "usd_net_value": format_usd(usd_net_value)})
    LIVE = all_data
    STATUS_DATA = status_data
    if mt5 > 0 or mt10 > 0:
        send_slack_message("balance", f"trades over 5%: {mt5}\ntrades over 10%: {mt10}")
    try:
        net_perc_profitable = round(net_profitable/len(raw)*100, 4)
    except ZeroDivisionError:
        net_perc_profitable = 0

    if net_perc_profitable <= 20 or net_perc_profitable >= 20:
        status = 2
        msg = "CRITICAL"
    elif net_perc_profitable <= 5 or net_perc_profitable >= 5:
        status = 1
        msg = "WARNING"
    elif -5 < net_perc_profitable < 5:
        status = 0
        msg = "OK"
    else:
        status = 3
        msg = "UNKNOWN"

    env = config.main.base_env
    text = (f"{msg}: {net_perc_profitable}% of open trades are "
           f"profitable|net_profitable={net_perc_profitable};20;10;;")

    push_prom_data(f'open_profitable_{env}', net_perc_profitable)
    push_prom_data(f'num_open_trades_{env}', len(raw))

    send_nsca(status=status, host_name="jenkins",
              service_name=f"{env}_open_profitable",
              text_output=text, remote_host="nagios.amrox.loc")

    return LIVE, STATUS_DATA

@APP.route('/live', methods=['GET', 'POST'])
@login_required
def live():
    """
    route to live data
    """
    files = {}
    if config.main.base_env == 'data':
        files['aggregate'] = (AGG_DATA, 1)
        files['double_rsi'] = (get_doublersi_list(), 4)
    else:
        files['open_trades'] =  (LIVE, 5)
        files['open_trade_status'] =  (STATUS_DATA, 5)
        files['balance'] = (BALANCE, 1)

    if request.method == 'GET':
        return render_template('data.html', files=files)
    if request.method == 'POST':
        req = request.form['submit']
        results, order =files[req]

        if results == []:
            return render_template('error.html', message="No available data")
        fieldnames = list(results[0].keys())
        return render_template('data.html', results=results, fieldnames=fieldnames, len=len,
                               files=files.keys(), order_column=order)
    return None

@APP.route('/menu', methods=["GET"])
@login_required
def menu():
    """
    Menu of strategies
    """
    length = get_pairs()[1]
    return render_template('menu.html', strats=length)

def get_total_values():
    """
    Get total current USD value of open trades from DB and exchange
    and sum net perc.
    return values as tupple
    """
    usd_trade_value = 0
    total_net_perc = 0
    usd_trade_amount = 0
    dbase = Mysql()
    raw = dbase.get_open_trades()
    commission = float(dbase.get_complete_commission())
    stream_req = requests.get('http://stream/5m/all', timeout=10)
    prices = stream_req.json()
    names = []
    for _, _, pair, name, open_price, direction, quote_in in raw:
        current_price = prices['recent'][pair]['close']
        perc = perc_diff(open_price, current_price)
        perc = -perc if direction == 'short' else perc
        net_perc = perc - commission
        names.append(name)

        current_amt = (float(quote_in)/100) * float(net_perc)
        current_quote = get_quote(pair)
        if current_quote == 'USDT':
            usd_trade_value += float(current_amt)
            usd_trade_amount += float(quote_in)
        else:
            usd_trade_value += base2quote(current_amt, current_quote+'USDT')
            usd_trade_amount += base2quote(quote_in, current_quote+'USDT')
        total_net_perc += net_perc
    name_count = dict(Counter(names))
    for key, val in name_count.items():
        push_prom_data(f'num_open_trades_{key}_{config.main.base_env}', val)
    return usd_trade_value, total_net_perc, usd_trade_amount

@APP.route('/refresh_data')
@login_required
def refresh_data():
    """
    Route to manually call functions to refresh all data
    in the background and return nothing
    """
    get_balance()
    get_live()
    get_data()
    get_additional_details()
    return Response(status=200)

@APP.route('/values')
@login_required
def get_values():
    """
    return raw contents of global values var
    """
    return VALUES

@decorator_timer
def get_additional_details():
    """
    Get tp/sl and drawup/drawdown from redis and mysql
    """
    redis=Redis()
    dbase = Mysql()

    trades = dbase.get_open_trades()
    for item in trades:
        _, interval, pair, name, _, direction, _ = item

        VALUES['drawup'][f"{pair}:{name}:{direction}"] = \
                redis.get_drawup(pair, name=name, interval=interval, direction=direction)['perc']

        VALUES['drawdown'][f"{pair}:{name}:{direction}"] = \
                redis.get_drawdown(pair, name=name, interval=interval, direction=direction)['perc']

        try:
            VALUES['take'][f"{pair}:{name}:{direction}"] = redis.get_on_entry(pair,
                                                                              'take_profit_perc',
                                                                              name=name,
                                                                              interval=interval,
                                                                              direction=direction)

            VALUES['stop'][f"{pair}:{name}:{direction}"] = redis.get_on_entry(pair,
                                                                              'stop_loss_perc',
                                                                              name=name,
                                                                              interval=interval,
                                                                              direction=direction)
        except KeyError:
            pass

@decorator_timer
def get_balance():
    """
    Get cross margin quote amounts from exchange
    """
    global BALANCE
    all_results = []

    now = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    total_value, total_net_perc, usd_trade_amount = get_total_values()
    current_net_perc = round(total_net_perc, 4)

    # default values for non-prod envs
    risk = 999
    max_borrow_usd = 0
    total_debts_usd = 0
    current_balance_usd = 0
    current_balance_btc = 0
    ###

    if str2bool(config.main.production):
        debts = {}
        free = {}
        risk = get_cross_margin_level()
        balance = Balance(test=False)
        wallet = balance.get_saved_balance()
        client=binance_auth()
        details = client.get_cross_margin_details()
        for item in details['userAssets']:
            debt = float(item['borrowed']) + float(item['interest'])
            if debt > 0:
                debts[item['asset']] = debt
            if float(item['free']) > 0:
                free[item['asset']] = float(item['free'])
        max_borrow_usd = client.get_max_borrow()
        current_balance_usd = wallet['total_USD']
        current_balance_btc = wallet['total_BTC']

        all_results.append({'key': 'avail_borrow', 'usd': format_usd(max_borrow_usd),
                            'val': ''})
        all_results.append({'key': 'risk', 'usd': 0,
                            'val': risk})
        all_results.append({'key': 'current_balance', 'usd': current_balance_btc,
                            'val': current_balance_btc})
        total_debts_usd = 0
        for key, val in debts.items():
            usd_debt = val if 'USD' in key else base2quote(val, key+'USDT')
            all_results.append({'key': f'{key} debt', 'usd': f'{format_usd(usd_debt)}',
                                'val': f'{val:.5f}'})
            total_debts_usd += usd_debt
        if total_debts_usd > 0:
            all_results.append({'key':'total_debts', 'usd': f'{format_usd(total_debts_usd)}',
                                'val': ''})

        for key, val in free.items():
            usd_free = val if 'USD' in key else base2quote(val, key+'USDT')
            all_results.append({'key': f'{key} free', 'usd': format_usd(usd_free),
                                'val': f'{val:.5f}'})

    all_results.append({'key': 'current_trade_value', 'usd': format_usd(total_value),
                        'val': '0'})
    all_results.append({'key': 'current_trade_amount', 'usd': format_usd(usd_trade_amount),
                        'val': '0'})
    all_results.append({'key': 'current_net_perc', 'usd': '',
                        'val': current_net_perc})
    all_results.append({'key': 'last_updated', 'usd': '', 'val': now})

    if current_net_perc < -20 or current_net_perc > 20:
        status = 2
        msg = "CRITICAL"
    elif current_net_perc <= 10 or current_net_perc >= 10:
        status = 1
        msg = "WARNING"
    elif 10 < current_net_perc < 10:
        status = 0
        msg = "OK"
    else:
        status = 3
        msg = "UNKNOWN"

    env = config.main.base_env
    text = f"{msg}: Current_net_perc is {current_net_perc}%|net_perc={current_net_perc};0;-25;;"

    prom_data = {f'open_net_perc_{env}': current_net_perc,
                 f'open_net_profit_{env}': total_value,
                 f'risk_factor_{env}': risk,
                 f'max_borrow_usd_{env}': max_borrow_usd,
                 f'total_debts_usd_{env}': total_debts_usd,
                 f'total_debts_usd_{env}': total_debts_usd,
                 f'current_balance_usd_{env}': price2float(current_balance_usd),
                 f'current_balance_btc_{env}': price2float(current_balance_btc)}
    for k, v in prom_data.items():
        push_prom_data(k,v)
    send_nsca(status=status, host_name="jenkins",
              service_name=f"{env}_open_net_perc",
              text_output=text, remote_host="nagios.amrox.loc")

    BALANCE = all_results

@decorator_timer
def get_data():
    """
    extract candles & indicators from data api
    """
    for tf in ('15m', '1h'):
        DATA[f'tf_{tf}'] = AttributeDict(requests.get(f'http://www.data.amrox.loc/data/{tf}',
                                                      timeout=10).json())

@arg_decorator
def main():
    """API for interacting with trading system"""

    setproctitle(f"{config.main.base_env}-api_dashboard")
    scheduler = BackgroundScheduler() # Create Scheduler
    if config.main.base_env.strip() != 'data':
        scheduler.add_job(func=get_additional_details, trigger="interval", minutes=3)
        scheduler.add_job(func=get_balance, trigger="interval", minutes=3)
        scheduler.add_job(func=get_live, trigger="interval", minutes=3)
        scheduler.add_job(func=get_data, trigger="interval", minutes=3,
                          next_run_time=datetime.now()+timedelta(seconds=10))
    else:
        scheduler.add_job(func=get_doublersi, trigger="interval", minutes=3)
        scheduler.add_job(func=get_agg, trigger="interval", minutes=3)
    scheduler.start() # Start Scheduler

    logging.basicConfig(level=logging.ERROR)
    if float(config.main.logging_level) > 10:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True
    APP.run(debug=False, host='0.0.0.0', port=5000, threaded=True)

if __name__ == '__main__':
    main()
