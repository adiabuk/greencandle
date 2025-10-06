#!/usr/bin/env python
#pylint: disable=no-member,broad-except,no-name-in-module,too-many-statements,too-many-branches

"""
API routing module
"""
import time
import sys
import os
import json
from pathlib import Path
import logging
import requests
from flask import Flask, request, Response
from setproctitle import setproctitle
from redis.commands.json.path import Path as json_path
from greencandle.lib.common import arg_decorator, get_short_name
from greencandle.lib import config
from greencandle.lib.logger import get_logger
from greencandle.lib.mysql import Mysql
from greencandle.lib.redis_conn import Redis

config.create_config()
TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')
APP = Flask(__name__)
LOGGER = get_logger(__name__)
TOKEN = config.web.api_token

def send_trade(payload, host, subd='/webhook'):
    """
    send trade to specified host
    """
    url = f"http://{host}:20000/{subd}"
    try:
        LOGGER.info("calling url %s - %s ", url, str(payload))
        requests.post(url, json=payload, timeout=20)
    except Exception as exc:
        LOGGER.critical("unable to call url: %s - %s", url, str(exc))

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

def forward(payload):
    """
    Forward request to another environment
    """
    env = payload['env']
    host = payload['host'] if 'host' in payload else f'www.{env}.amrox.loc'
    payload['strategy'] = 'alert' if env == 'alarm' else payload['strategy']
    command = f"configstore package get --basedir /srv/greencandle/config {env} api_token"
    LOGGER.info("forwarding request to %s - %s ",env, str(payload))
    token = os.popen(command).read().split()[0]
    payload['edited'] = "yes"
    url = f"https://{host}/{token}"
    try:
        requests.post(url, json=payload, timeout=20, verify=False)
    except requests.exceptions.RequestException:
        pass
    return Response(status=200)

@APP.route(f'/{TOKEN}', methods=['POST'])
def respond():
    """
    Default route to trade
    """
    payload = request.json
    if payload['strategy'] == 'close_all' and payload['env'] != config.main.base_env:
        forward(payload)
        return Response(status=200)
    with open('/etc/router_config.json', 'r', encoding='utf-8') as json_file:
        router_config = json.load(json_file)
    if payload['strategy'] == 'close_all':
        name = get_short_name(payload['name'], payload['env'], payload['direction'])
        send_trade(payload, name, subd='/close_all')
        return Response(status=200)

    if 'pair' in payload and payload['pair'] == 'No pair':
        LOGGER.debug("request received: %s", payload)
    else:
        LOGGER.info("request received: %s", payload)
    try:
        containers = router_config[payload["strategy"].strip()]
    except TypeError:
        LOGGER.critical("invalid router_config or payload detected: %s", payload)
        return Response(status=500)
    except KeyError:
        LOGGER.critical("invalid or missing strategy %s", str(payload))
        return Response(status=500)
    if not any(valid in str(payload['action']).strip() for valid in ['0', '1', '-1',
                                                                     'open', 'close']):
        LOGGER.critical("Invalid action detected in payload %s", str(payload))
        return Response(status=500)

    if payload["strategy"] == "route":
        Path(f'/var/run/router-{config.main.base_env}').touch()
        return Response(status=200)

    env = config.main.base_env
    alert_drain = Path('/var/local/drain/{env}_alert_drain').is_file()
    for container in containers:
        if container == 'alert' and not alert_drain:
            # change strategy
            # so we don't create an infinate API loop
            payload['strategy'] = 'alert'
            payload['env'] = 'alarm'

            # add environment name to text
            if 'environment' not in payload['text']:
                payload['text'] += f'. {env} environment'

            payload['edited'] = "yes"
        payload['pair'] = payload['pair'].lower()
        if ':' in container:
            new_env, new_strategy = container.split(':')
            payload['env'] = new_env
            payload['strategy'] = new_strategy
            route_drain = Path(f'/var/local/drain/drain_{new_env}_{new_strategy}').is_file()
            if route_drain:
                LOGGER.warning('skipping forwarding to %s:%s due to drain', new_env, new_strategy)
            else:
                forward(payload)

        elif 'env' not in payload or payload['env'] == env:
            send_trade(payload, container)
        elif 'queue' in container:
            redis = Redis(db=14)
            redis.conn.json().set(int(time.time()), json_path.root_path(), payload)
            del redis
        else:
            forward(payload)

    mysql = Mysql()
    try:
        mysql.insert_api_trade(**request.json)
    except KeyError:
        LOGGER.critical("missing required field in json: %s", str(request.json))

    return Response(status=200)

@arg_decorator
def main():
    """
    Route trades from api dashboard to one or more containers
    Config is /etc/router_config.json

    Usage: api_router
    """
    requests.packages.urllib3.disable_warnings()
    setproctitle(f"{config.main.base_env}-api_router")
    logging.basicConfig(level=logging.ERROR)
    if float(config.main.logging_level) > 10:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True
    APP.run(debug=False, host='0.0.0.0', port=1080, threaded=True)

if __name__ == "__main__":
    main()
