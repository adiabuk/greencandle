#!/usr/bin/env python
#pylint: disable=no-member
"""
Flask module for getting fetching and setting drain status
"""
import time
from datetime import datetime
from flask import Flask, request, Response
from str2bool import str2bool
from send_nsca3 import send_nsca
from redis.commands.json.path import Path
from greencandle.lib.common import arg_decorator
from greencandle.lib.objects import AttributeDict
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger
from greencandle.lib.web import find_paths


LOGGER = get_logger(__name__)
APP = Flask(__name__, template_folder="/var/www/html", static_url_path='/',
            static_folder='/var/www/html')
#APP.wsgi_app = PrefixMiddleware(APP.wsgi_app, prefix='/drain')

ENVS = ["prod", "stag", "per", "data", "test", "dev"]

DEF_STRUCT = {
              "slack": False,
              "tf_top": {"long": False, "short":False, "close": False},
              "tf_1m": {"long": False, "short":False, "close": False},
              "tf_5m": {"long": False, "short":False, "close": False},
              "tf_15m": {"long": False, "short":False, "close": False},
              "tf_30m": {"long": False, "short":False, "close": False},
              "tf_1h": {"long": False, "short":False, "close": False},
              "tf_4h": {"long": False, "short":False, "close": False},
              "tf_12h": {"long": False, "short":False, "close": False},
              "tf_1d": {"long": False, "short":False, "close": False}
              }

def get_struct(env):
    """
    fetch drain config for given environment from redis
    if it doesn't exist, use default config, and update redis with default values
    """
    redis = Redis()
    struct = redis.conn.json().get(env)
    if not struct:
        struct = DEF_STRUCT
        redis.conn.json().set(env, Path.root_path(), struct)
    return AttributeDict(struct)

def set_struct(env, struct):
    """
    set/update structure for given environment in redis
    """
    redis = Redis()
    redis.conn.json().set(env, Path.root_path(), struct)


@APP.route('/queue/add', methods=["POST"])
def add_to_queue():
    """
    Add trade to queue
    """
    payload = AttributeDict(request.json)
    redis = Redis(db=1)
    key = int(time.time())
    redis.conn.json().set(key, Path.root_path(), payload)

@APP.route('/queue/get_all', methods=["GET"])
def get_all_queued():
    """
    Fetch all trades in the queue
    """
    queued = {}
    redis = Redis(db=1)
    keys = redis.conn.keys()
    for key in keys():
        queued[key] = redis.conn.json().get(key)
    return queued


APP.route('/drain/get_slack', methods=["GET"])
def get_slack_drain():
    """
    Get slack drain status for given env
    """
    env = request.args.get('env')
    if env not in ENVS:
        return Response(response=f'Invalid Environment: {env}', status=400)
    struct = get_struct(env)

    result = struct[f'tf_{env}']['slack']

    return {'result':result}

@APP.route('/drain/get_all', methods=["GET"])
def get_all_envs():
    """
    Get entire drain structure for all envs
    """
    entire = {}
    for env in ENVS:
        entire[env] = get_struct(env)
    return entire

@APP.route('/drain/drain_count', methods=["GET"])
def get_drain_count():
    """
    Get drain count and
    """
    env = request.args.get('env', False)
    struct = get_struct(env)
    paths = [':'.join(item).rsplit('_', maxsplit=1)[-1] for item in find_paths(struct, True)]
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    results = "none" if not paths else ", ".join(paths)
    return {'count': len(paths), 'result': results, 'current_time': current_time,
            'env': env}

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

@APP.route('/drain/set_value', methods=["POST"])
def set_value():
    """
    update a boolean drain value for a given env/direction/interval
    """
    payload = AttributeDict(request.json)
    struct = get_struct(payload.env)
    struct[f'tf_{payload.interval}'][payload.direction] = str2bool(str(payload.value)) if \
                payload.value is not None else False
    set_struct(payload.env, struct)
    return Response(status=200)

@APP.route('/drain/get_envs', methods=["GET"])
def get_envs():
    """
    Return a list of supported envs
    """
    return ENVS

@APP.route('/drain/get_env', methods=["GET"])
def get_env():
    """
    get structure for a given environment
    """
    env = request.args.get('env')
    if env not in ENVS:
        return Response(response=f'Invalid Environment: {env}', status=400)
    struct = get_struct(env)
    return struct

@APP.route('/drain/get_value', methods=["GET"])
def get_value():
    """
    Get true/false value of drain status for a given env/direction/interval
    Also takes into account global overries for a given environment
    """

    direction = request.args.get('direction')
    env = request.args.get('env')
    interval = request.args.get('interval')
    if env not in ENVS:
        return Response(response=f'Invalid Environment: {env}', status=400)

    struct = get_struct(env)

    result = struct[f'tf_{interval}'][direction] or struct['tf_top'][direction]
    LOGGER.info("Fetching value for %s %s %s : %s", direction, interval, env, result)

    return {'result':result}

@APP.route('/nagios/push_alert', methods=["POST"])
def push_nagios_alert():
    """
    Receive alert payload from grafana (or any other alert generator)
    and forward to nagios via nsca
    """
    payload = request.json

    for alert in payload['alerts']:
        if not alert['values']:
            continue
        LOGGER.info('Processing incoming alert: %s %s %s', alert['labels']['alertname'],
                    alert['status'], alert['values']['A'])
        status = 2 if 'firing' in alert['status'] else 0

        send_nsca(status=status, host_name='eaglenest',
                  service_name=alert['labels']['alertname'],
                  text_output=f"Alert from webhook: {alert['values']['A']}",
                  remote_host='nagios.amrox.loc')

    return Response(status=200)

@arg_decorator
def main():
    """
    API for determining fetching and setting drain settings for all environments
    settings can be at env level (top_open, top_close)
    or per interval/direction
    Data is stored in redis as a JSON object
    """
    APP.run(debug=False, host='0.0.0.0', port=6000, threaded=True)

if __name__ == '__main__':
    main()
