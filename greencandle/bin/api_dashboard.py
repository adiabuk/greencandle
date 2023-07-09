#!/usr/bin/env python
#pylint: disable=bare-except,no-member,wrong-import-position,no-else-return,unnecessary-comprehension

"""
Flask module for manipulating API trades and displaying relevent graphs
"""
import re
import os
import json
import subprocess
from collections import defaultdict
import requests
from flask import Flask, render_template, request, Response, redirect, url_for
from flask_login import LoginManager, login_required
APP = Flask(__name__, template_folder="/etc/gcapi", static_url_path='/',
            static_folder='/etc/gcapi')
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator, divide_chunks, get_be_services, list_to_dict
from greencandle.lib import config
from greencandle.lib.flask_auth import load_user, login as loginx, logout as logoutx
config.create_config()

LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.init_app(APP)
LOGIN_MANAGER.login_view = "login"
APP.config['SECRET_KEY'] = os.environ['SECRET_KEY'] if 'SECRET_KEY' in os.environ else \
        os.urandom(12).hex()
LOAD_USER = LOGIN_MANAGER.user_loader(load_user)
LOGIN = APP.route("/login", methods=["GET", "POST"])(loginx)
LOGIN = APP.route("/logout", methods=["GET", "POST"])(logoutx)

SCRIPTS = ["write_balance", "get_quote_balance", "get_active_trades", "get_trade_status",
           "get_hour_profit", "repay_debts", "balance_graph", "test_close", "close_all"]

def get_pairs(env=config.main.base_env):
    """
    get details from docker_compose, configstore, and router config
    output in reversed JSON format

    Usage: api_dashboard
    """
    docker_compose = open("/srv/greencandle/install/docker-compose_{}.yml"
                          .format(env), "r")
    pairs_dict = {}
    names = {}
    length = defaultdict(int)
    pattern = "CONFIG_ENV"
    for line in docker_compose:
        if re.search(pattern, line.strip()) and not line.strip().endswith(('prod', 'api', 'cron')):
            env = line.split('=')[1].strip()
            command = ('configstore package get --basedir /srv/greencandle/config {} pairs'
                       .format(env))
            result = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            pairs = result.stdout.read().split()
            command = ('configstore package get --basedir /srv/greencandle/config {} name'
                       .format(env))
            result = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            name = result.stdout.read().split()
            pairs_dict[env] = [pair.decode('utf-8') for pair in pairs]
            length[env] += 1
            names[env] = name[0].decode('utf-8')
    for key, val in pairs_dict.items():
        length[key] = len(val)
    return pairs_dict, dict(length), names

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
    return render_template('commands.html', scripts=SCRIPTS)

@APP.route('/internal', methods=["GET"])
@login_required
def interal():
    """Load internal page"""
    page = "http://" + request.args.get('page')
    resp = requests.get(f'{page}')
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
    if command.strip() in SCRIPTS:
        subprocess.Popen(command)
    return redirect(url_for('commands'))

@APP.route('/charts', methods=["GET"])
@login_required
def charts():
    """Charts for given strategy/config_env"""
    config_env = request.args.get('config_env')
    groups = list(divide_chunks(get_pairs()[0][config_env], 2))

    return render_template('charts.html', groups=groups)

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
    send_trade(pair, strategy, trade_action, take=take, stop=stop)
    if close:
        return '<button type="button" onclick="window.close()">Close Tab</button>'
    else:
        return redirect(url_for('trade'))

def send_trade(pair, strategy, trade_action, take=None, stop=None):
    """
    Create OPEN/CLOSE post request and send to API router
    """
    payload = {"pair": pair,
               "text": "Manual {} action from API".format(trade_action),
               "action": trade_action,
               "strategy": strategy,
               "manual": True,
               "tp": take,
               "sl": stop}
    api_token = config.web.api_token
    url = "http://router:1080/{}".format(api_token)
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
                container = links_dict[name]
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

@APP.route('/data', methods=['GET', 'POST'])
def data():
    """
    route to data spreadsheets
    """
    files = ['middle_200', 'STOCHRSI_8', 'volume', 'distance_12', 'middle_12', 'stoch_flat',
             'candle_size', 'STX_200', 'bb_size', 'all', 'bbperc_diff', 'distance_200',
             'bbperc_200', 'stx_diff']
    if request.method == 'GET':
        return render_template('data.html', files=files)
    elif request.method == 'POST':
        results2 = []
        redis = Redis(db=3)
        keys = redis.conn.keys()
        function = request.form['submit']
        for key in keys:
            try:
                item = redis.conn.hmget(key, function.encode())[0].decode()
                if 'None' not in item:

                    pair, interval = key.decode().split(':')
                    results2.append({'pair':pair, 'interval': interval, function: item})
            except:
                continue

        fieldnames = [key for key in results2[0].keys()]

        return render_template('data.html', results=results2, fieldnames=fieldnames, len=len,
                               files=files)
    return None


@APP.route('/menu', methods=["GET"])
@login_required
def menu():
    """
    Menu of strategies
    """
    length = get_pairs()[1]
    return render_template('menu.html', strats=length)

@arg_decorator
def main():
    """API for interacting with trading system"""

    APP.run(debug=False, host='0.0.0.0', port=5000, threaded=True)

if __name__ == '__main__':
    main()
