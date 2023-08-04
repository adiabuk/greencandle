#!/usr/bin/env python
#pylint: disable=no-member,broad-except

"""
API routing module
"""

import sys
import os
import json
from pathlib import Path
import requests
from flask import Flask, request, Response
import setproctitle
from greencandle.lib.common import arg_decorator
from greencandle.lib import config
from greencandle.lib.logger import get_logger
from greencandle.lib.mysql import Mysql

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
        LOGGER.info("Calling url %s - %s ", url, str(payload))
        requests.post(url, json=payload, timeout=20)
    except Exception as exc:
        LOGGER.critical("Unable to call url: %s - %s", url, str(exc))

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

def forward(token):
    """
    Forward request to another environment
    """
    payload = request.json
    env = payload['env']
    payload['strategy'] = 'alert' if env == 'alarm' else payload['strategy']
    command = f"configstore package get --basedir /srv/greencandle/config {env} api_token"
    LOGGER.info("Forwarding request to %s - %s ",env, str(payload))
    token = os.popen(command).read().split()[0]
    payload['edited'] = "yes"
    url = f"https://{payload['host']}/{token}"
    try:
        requests.post(url, json=payload, timeout=5, verify=False)
    except requests.exceptions.RequestException:
        pass
    return Response(status=200)

@APP.route(f'/{TOKEN}', methods=['POST'])
def respond():
    """
    Default route to trade
    """
    payload = request.json
    with open('/etc/router_config.json') as json_file:
        router_config = json.load(json_file)

    LOGGER.info("Request received: %s", payload)
    try:
        containers = router_config[payload["strategy"].strip()]
    except TypeError:
        LOGGER.critical("Invalid router_config or payload detected: %s", payload)
        return Response(status=500)
    except KeyError:
        LOGGER.critical("Invalid or missing strategy %s", str(payload))
        return Response(status=500)

    if payload["strategy"] == "route":
        Path(f'/var/run/router-{config.main.base_env}').touch()
        return Response(status=200)

    env = config.main.base_env
    alert_drain = Path('/var/local/{env}_alert_drain').is_file()
    for container in containers:
        if container == 'alert' and not alert_drain:
            # change strategy
            # so we don't create an infinate API loop
            payload['strategy'] = 'alert'
            payload['env'] = 'alarm'
            payload['host'] = '10.8.0.1'

            # add environment name to text

            if 'environment' not in payload['text']:
                payload['text'] += f'.{env} environment'

            payload['edited'] = "yes"

        payload['pair'] = payload['pair'].lower()
        if 'env' not in payload or payload['env'] == env:
            send_trade(payload, container)
        elif ':' in container:
            new_env, new_strategy = container.split(':')
            payload['env'] = new_env
            payload['strategy'] = new_strategy
            payload['host'] = '10.8.0.1'
            route_drain = Path(f'/var/local/drain_{new_env}_{new_strategy}').is_file()
            if route_drain:
                LOGGER.warning('Skipping forwarding to %s:%s due to drain', new_env, new_strategy)
            else:
                forward(payload)

        else:
            payload['host'] = '10.8.0.1'
            forward(payload)

    mysql = Mysql()
    try:
        mysql.insert_api_trade(**request.json)
    except KeyError:
        LOGGER.critical("Missing required field in json: %s", str(request.json))

    return Response(status=200)

@arg_decorator
def main():
    """
    Route trades from api dashboard to one or more containers
    Config is /etc/router_config.json

    Usage: api_router
    """
    setproctitle.setproctitle("api_router")
    APP.run(debug=False, host='0.0.0.0', port=1080, threaded=True)
if __name__ == "__main__":
    main()
