#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,bare-except

"""
API routing module
"""

import sys
import json
import requests
from flask import Flask, request, Response
from greencandle.lib import config
config.create_config()
from greencandle.lib.logger import get_logger

TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')
APP = Flask(__name__)
LOGGER = get_logger(__name__)

def send_trade(payload, host):
    """
    send trade to specified host
    """
    url = "http://{}/webhook".format(host)
    try:
        LOGGER.info("Calling url:%s" % url)
        requests.post(url, json=payload,timeout=0.0000000001)
    except:
        pass


@APP.route('/webhook', methods=['POST'])
def respond():
    """
    Default route to trade
    """
    payload = request.json
    with open('/etc/router_config.json') as json_file:
        router_config = json.load(json_file)
    print(router_config)

    #for env, host in router_config.items():
    hosts = router_config[payload["strategy"]]
    for host in hosts:
        send_trade(payload, host)
    print(request.json)
    LOGGER.info("Request received: %s" %(request.json))
    return Response(status=200)

def main():
    """
    main function
    """
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("API for executing trades")
        sys.exit(0)

    APP.run(debug=True, host='0.0.0.0', port=80, threaded=True)
if __name__ == "__main__":
    main()
