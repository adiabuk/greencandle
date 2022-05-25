#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,bare-except

"""
API routing module
"""

import sys
import json
import requests
from flask import Flask, request, Response
from greencandle.lib.common import arg_decorator
from greencandle.lib import config
config.create_config()
from greencandle.lib.logger import get_logger
from greencandle.lib.mysql import Mysql

TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')
APP = Flask(__name__)
LOGGER = get_logger(__name__)
TOKEN = config.main.api_token

def send_trade(payload, host):
    """
    send trade to specified host
    """
    url = "http://{}:20000/webhook".format(host)
    try:
        LOGGER.info("Calling url:%s" % url)
        requests.post(url, json=payload, timeout=1)
    except:
        pass

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

@APP.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    """
    Default route to trade
    """
    payload = request.json
    with open('/etc/router_config.json') as json_file:
        router_config = json.load(json_file)

    try:
        hosts = router_config[payload["strategy"].strip()]
    except TypeError:
        LOGGER.error("Invalid JSON detected: %s" % payload)
        return Response(status=500)

    for host in hosts:
        if host == 'alert' and 'edited' not in payload:
            # change strategy
            # so we don't create an infinate API loop
            payload['strategy'] = 'alert'

            # add environment name to text
            env = config.main.base_env
            try:
                environment = {"per": "personal",
                               "prod": "production",
                               "stag": "staging",
                               "test":"testing",
                               "data":"data"}[env]
            except KeyError:
                environment = "unknown"
            payload['text'] += '...{} environment'.format(environment)
            payload['edited'] = "yes"


        send_trade(payload, host)
    LOGGER.info("Request received: %s" %(request.json))
    mysql = Mysql()
    try:
        mysql.insert_api_trade(**request.json)
    except KeyError:
        logger.error("Missing required field in json: %s" % str(request.json))

    return Response(status=200)

@arg_decorator
def main():
    """
    Route trades from api dashboard to one or more containers
    Config is /etc/router_config.json

    Usage: api_router
    """
    APP.run(debug=True, host='0.0.0.0', port=1080, threaded=True)
if __name__ == "__main__":
    main()
