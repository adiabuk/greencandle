#!/usr/bin/env python
#pylint: disable=bare-except,no-member,consider-using-with,too-many-locals,assigning-non-slot,global-statement

"""
Flask module for manipulating API trades and displaying relevent graphs
"""
import re
import os
import json
import time
import subprocess
import logging
from collections import defaultdict
from datetime import timedelta, datetime
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request, Response, redirect, url_for, session, g
from flask_login import LoginManager, login_required, current_user
import setproctitle
from greencandle.lib.redis_conn import Redis
from greencandle.lib.auth import binance_auth
from greencandle.lib.mysql import Mysql
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.binance_accounts import base2quote
from greencandle.lib.common import (arg_decorator, divide_chunks, get_be_services, list_to_dict,
                                    perc_diff, get_tv_link, get_trade_link, format_usd)
from greencandle.lib import config
from greencandle.lib.flask_auth import load_user, login as loginx, logout as logoutx

config.create_config()
APP = Flask(__name__, template_folder="/etc/gcapi", static_url_path='/',
            static_folder='/etc/gcapi')
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

SCRIPTS = ["write_balance", "get_quote_balance", "repay_debts", "get_risk", "get_trade_status",
           "get_hour_profit", "repay_debts", "balance_graph", "test_close"]
ARG_SCRIPTS = {"close_all": ['name_filter', 'threshold']}

def get_pairs(env=config.main.base_env):
    """
    get details from docker_compose, configstore, and router config
    output in reversed JSON format

    Usage: api_dashboard
    """
    docker_compose = open(f"/srv/greencandle/install/docker-compose_{env}.yml", "r")
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
    return render_template('commands.html', scripts=SCRIPTS, arg_scripts=ARG_SCRIPTS)

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

    if command.strip() in SCRIPTS:
        subprocess.Popen(command)
    if any(command.strip() in sublist for sublist in ARG_SCRIPTS):
        args = {key: value[0] for key, value in args.items() if value[0].strip() !=""}
        for key, value in args.items():
            # add args to command
            command += f' --{key} {value}'
        subprocess.Popen(command.split())
    return redirect(url_for('commands'))

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
    redis = Redis(db=6)
    pair = request.args.get('pair')
    interval = request.args.get('interval')
    redis.conn.delete(f'{pair}:{interval}')

    return redirect(url_for('extras'))

def sredis():
    """
    save rule into redis set
    """

    redis = Redis.conn(db=7)
    rule = request.args.get('rule')
    redis.conn.sadd(rule.strip())

    return redirect(url_for('extras'))


@APP.route("/extras", methods=['POST', 'GET'])
@login_required
def extras():
    """
    Form for entring new open|close trade rules
    and table for displaying current rules stored in redis
    """

    redis = Redis(db=6)
    data = []
    keys = redis.conn.keys()
    with open('/etc/router_config.json', 'r') as json_file:
        router_config = json.load(json_file)
    routes = [x for x in router_config.keys() if ('extra' in x or 'alert' in x)]

    for key in keys:
        current = json.loads(redis.conn.get(key).decode())
        pair = current['pair']
        interval=current['interval']
        current['pair'] = get_tv_link(pair, interval, anchor=True)

        delete_button = (f'<form method=post action=/xredis?pair={pair}&interval={interval}><input '
                          'type=submit name=delete value=delete></form>')
        save_button = (f'<form method=post action=/sredis?pair={pair}&interval={interval}><input '
                        'type=submit name=save value=save></form>')
        current.update({'tasks': f'{save_button}{delete_button}'})
        add_time = datetime.fromtimestamp(int(key)).strftime('%c')
        current.update({'add_time': add_time})
        data.append(current)

    if request.method == 'POST':
        args = request.form.to_dict(flat=False)
        args = {key: value[0] for key, value in args.items() if value[0].strip() !=""}
        args.popitem() #remove submit button
        args = defaultdict(str, args)  # enforce field with empty string if not present

        fields = ['pair', 'interval', 'action', 'usd', 'tp', 'sl', 'rule', 'forward_to']
        data_str = json.dumps({x:args[x] for x in fields})

        redis.conn.set(f"{str(int(time.time()))}", data_str)
        time.sleep(2)
        return redirect(url_for('extras'))


    return render_template('extras.html', data=data, routes=routes)

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
    take = request.args.get('tp') if 'tp' in request.args else None
    stop = request.args.get('sl') if 'sl' in request.args else None
    usd = request.args.get('usd') if 'usd' in request.args else None

    send_trade(pair, strategy, trade_action, take=take, stop=stop, usd=usd)
    return redirect(url_for('trade'))

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
    except:
        pass

@APP.route('/trade', methods=["GET"])
@login_required
def trade():
    """
    open/close actions for API trades
    """
    pairs, _, names = get_pairs()

    rev_names = {v: k for k, v in names.items()}
    with open('/etc/router_config.json', 'r') as json_file:
        router_config = json.load(json_file)

    env = config.main.base_env
    links_list = get_be_services(env)
    links_dict = list_to_dict(links_list, reverse=True, str_filter='-be-')

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

def get_agg():
    """
    collate aggregate data from redis
    """
    all_data = []
    redis = Redis(db=3)
    keys = redis.conn.keys()
    columns = ['distance_200', 'candle_size', 'avg_candles', 'sum_candles', 'macd_xover',
               'macd_diff', 'middle_200', 'bb_size', 'stoch_flat', 'num', 'bb_size',
               'bbperc_diff', 'bbperc', 'rsi', 'atrp', 'empty_count', 'stx_diff', 'date']
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

    return all_data

def get_live():
    """
    Get live open trade details
    """
    global LIVE

    if config.main.base_env.strip() == 'data':
        return None
    all_data = []
    mt3 = 0
    mt5 = 0

    dbase = Mysql()
    stream = os.environ['STREAM']
    stream_req = requests.get(stream, timeout=10)
    prices = stream_req.json()

    services = list_to_dict(get_be_services(config.main.base_env),
                            reverse=False, str_filter='-be-')
    raw = dbase.get_open_trades()
    commission = float(dbase.get_complete_commission())

    for open_time, interval, pair, name, open_price, direction in raw:
        current_price = prices['recent'][pair]['close']
        perc = perc_diff(open_price, current_price)
        perc = -perc if direction == 'short' else perc
        net_perc = perc - commission

        if float(net_perc) > 3:
            mt3 += 1
        if float(net_perc) > 5:
            mt5 += 1

        trade_direction = f"{name}-{direction}" if \
                not (name.endswith('long') or name.endswith('short')) else name

        short_name = services[trade_direction]
        close_link = get_trade_link(pair, short_name, 'close', 'close_now',
                              config.web.nginx_port, anchor=True, short=True)
        take = get_value('take', pair, name, direction)
        stop = get_value('stop', pair, name, direction)
        drawup = get_value('drawup', pair, name, direction)
        drawdown = get_value('drawdown', pair, name, direction)

        all_data.append({"pair": get_tv_link(pair, interval, anchor=True),
                         "interval": interval,
                         "open_time": open_time,
                         "name": short_name,
                         "perc": f'{round(perc,4)}',
                         "net_perc": f'{round(net_perc,4)}',
                         "close": close_link,
                         "open_price": '{:g}'.format(float(open_price)),
                         "current_price": '{:g}'.format(float(current_price)),
                         "tp/sl": f"{take}/{stop}",
                         "du/dd": f"{round(drawup,2)}/{round(drawdown,2)}" })
    LIVE = all_data
    if mt3 > 0 or mt5 > 0:
        send_slack_message("balance", f"trades over 3%: {mt3}\ntrades over 5%: {mt5}")
    return LIVE

@APP.route('/live', methods=['GET', 'POST'])
@login_required
def live():
    """
    route to live data
    """
    files = {'open_trades': (get_live(), 4), 'aggregate': (get_agg(), 1), 'balance':(BALANCE, 1)}

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

def get_additional_details():
    """
    Get tp/sl and drawup/drawdown from redis and mysql
    """
    redis=Redis()
    dbase = Mysql()

    trades = dbase.get_open_trades()
    global VALUES
    for item in trades:
        _, interval, pair, name, _, direction = item

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

def get_balance():
    """
    Get cross margin quote amounts from exchange
    """
    global BALANCE
    client=binance_auth()
    all_results = []
    details = client.get_cross_margin_details()
    debts = {}
    free = {}
    for item in details['userAssets']:
        debt = float(item['borrowed']) + float(item['interest'])
        if debt > 0:
            debts[item['asset']] = debt
        if float(item['free']) > 0:
            free[item['asset']] = float(item['free'])

    all_results.append({'key': 'avail_borrow', 'usd': format_usd(client.get_max_borrow()),
                        'val': ''})
    usd_debts_total = 0
    for key, val in debts.items():
        usd_debt = val if 'USD' in key else base2quote(val, key+'USDT')
        all_results.append({'key': f'{key} debt', 'usd': f'{format_usd(usd_debt)}',
                            'val': f'{val:.5f}'})
        usd_debts_total += usd_debt
    if usd_debts_total > 0:
        all_results.append({'key':'total_debts', 'usd': f'{format_usd(usd_debts_total)}',
                            'val': ''})

    for key, val in free.items():
        usd_free = val if 'USD' in key else base2quote(val, key+'USDT')
        all_results.append({'key': f'{key} free', 'usd': format_usd(usd_free),
                            'val': f'{val:.5f}'})
    BALANCE = all_results

@arg_decorator
def main():
    """API for interacting with trading system"""

    setproctitle.setproctitle("api_dashboard")

    if config.main.base_env.strip() != 'data':
        scheduler = BackgroundScheduler() # Create Scheduler
        scheduler.add_job(func=get_additional_details, trigger="interval", seconds=15)
        scheduler.add_job(func=get_balance, trigger="interval", minutes=10)
        scheduler.add_job(func=get_live, trigger="interval", minutes=2)
        get_balance()
        logging.basicConfig(level=logging.ERROR)
        scheduler.start() # Start Scheduler
    APP.run(debug=False, host='0.0.0.0', port=5000, threaded=True)

if __name__ == '__main__':
    main()
