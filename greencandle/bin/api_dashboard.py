#!/usr/bin/env python
#pylint: disable=bare-except, no-member, wrong-import-position
#pylint: disable=invalid-name  #FIXME
"""
Flask module for manipulating API trades and displaying relevent graphs
"""
import re
import os
import json
import subprocess
from collections import defaultdict
import requests
import yaml
from flask import Flask, render_template, request, Response, redirect, url_for
from flask_login import LoginManager, login_required
APP = Flask(__name__, template_folder="/etc/gcapi", static_url_path='/',
            static_folder='/etc/gcapi')
from greencandle.lib.common import arg_decorator
from greencandle.lib import config
from greencandle.lib.flask_auth import load_user, login as loginx, logout as logoutx
config.create_config()

LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.init_app(APP)
LOGIN_MANAGER.login_view = "login"
APP.config['SECRET_KEY'] = os.environ['SECRET_KEY'] if 'SECRET_KEY' in os.environ else \
        os.urandom(12).hex()
load_user = LOGIN_MANAGER.user_loader(load_user)
login = APP.route("/login", methods=["GET", "POST"])(loginx)
login = APP.route("/logout", methods=["GET", "POST"])(logoutx)

SCRIPTS = ["write_balance", "get_quote_balance", "get_active_trades", "get_trade_status",
           "get_hour_profit"]

def get_pairs():
    """
    get details from docker_compose, configstore, and router config
    output in reversed JSON format

    Usage: api_dashboard
    """
    docker_compose = open("/srv/greencandle/install/docker-compose_{}.yml"
                          .format(os.environ['HOST'].lower()), "r")
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

def divide_chunks(lst, num):
    """
    Divide list into lists of lists
    using given chunk size
    """

    # looping till length l
    for i in range(0, len(lst), num):
        yield lst[i:i + num]

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

@APP.route('/example', methods=["GET"])
@login_required
def example():
    """Load page in an iframe"""
    page = "example.com"
    return render_template('iframe.html', page=page)


@APP.route('/run', methods=["POST"])
@login_required
def run():
    """
    Run command from web
    """
    command = request.args.get('command')
    if command.strip() in SCRIPTS:
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()
    return redirect(url_for('commands'))


@APP.route('/charts', methods=["GET"])
@login_required
def charts():
    """Charts for given strategy/config_env"""
    config_env = request.args.get('config_env')
    groups = list(divide_chunks(get_pairs()[0][config_env], 2))

    return render_template('charts.html', groups=groups)

def list_to_dict(rlist):
    """
    Convert colon seperated string list to key/value dict
    """
    links = dict(map(lambda s: s.split(':'), rlist))
    return {v: k for k, v in links.items() if "-be-" in k}

@APP.route("/action", methods=['POST', 'GET'])
@login_required
def action():
    """
    get buy/sell request
    """
    pair = request.args.get('pair')
    strategy = request.args.get('strategy')
    trade_action = request.args.get('action')
    close = request.args.get('close')
    send_trade(pair, strategy, trade_action)

    if close:
        return '<button type="button" onclick="window.close()">Close Tab</button>'
    else:
        return redirect(url_for('trade'))

def send_trade(pair, strategy, trade_action):
    """
    Create BUY/SELL post request and send to API router
    """
    payload = {"pair": pair,
               "text": "Manual {} action from API".format(trade_action),
               "action": trade_action,
               "strategy": strategy,
               "manual": True}
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
    Buy/sell actions for API trades
    """
    pairs, _, names = get_pairs()

    rev_names = {v: k for k, v in names.items()}
    with open('/etc/router_config.json', 'r') as json_file:
        router_config = json.load(json_file)

    with open("/srv/greencandle/install/docker-compose_{}.yml"
              .format(os.environ['HOST'].lower()), "r") as stream:
        try:
            output = (yaml.safe_load(stream))
        except yaml.YAMLError as exc:
            print(exc)
    env = config.main.base_env
    links_list = output['services']['{}-be-api-router'.format(env)]['links']
    links_dict = list_to_dict(links_list)

    my_dic = defaultdict(set)
    for strat, short_name in router_config.items():
        for item in short_name:
            name = item.split(':')[0]
            if name == 'alert':
                # use same format for alert redirection
                container = "{}-be-alert".format(env)
            else:
                container = links_dict[name]

            if container.startswith('{}-be-'.format(env)) and 'alert' not in container:
                actual_name = container.replace('-be', '')  # strip off container type
            else:
                continue
            config_env = rev_names[actual_name]
            xxx = pairs[config_env]
            my_dic[strat] |= set(xxx)

    return render_template('action.html', my_dic=my_dic)

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

    APP.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

if __name__ == '__main__':
    main()
