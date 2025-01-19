#!/usr/bin/env python
#pylint: disable=no-member
"""
Flask module for getting fetching and setting drain status
"""
from flask import Flask, request, Response
from str2bool import str2bool
from redis.commands.json.path import Path
from greencandle.lib.common import AttributeDict, arg_decorator
from greencandle.lib.redis_conn import Redis
from greencandle.lib.web import PrefixMiddleware

APP = Flask(__name__, template_folder="/var/www/html", static_url_path='/',
            static_folder='/var/www/html')
APP.wsgi_app = PrefixMiddleware(APP.wsgi_app, prefix='/drain')

DEF_STRUCT = {"top_open": False,
          "top_close": False,
          "tf_1m": {"long": False, "short":False, "close": False},
          "tf_5m": {"long": False, "short":False, "close": False},
          "tf_15m": {"long": False, "short":False, "close": False},
          "tf_30m": {"long": False, "short":False, "close": False},
          "tf_1h": {"long": False, "short":False, "close": False},
          "tf_4h": {"long": False, "short":False, "close": False},
          "tf_12h": {"long": False, "short":False, "close": False},
          "tf_1d": {"long": False, "short":False, "close": False}
          }

ENVS = ["prod", "stag", "per", "data", "test"]

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

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

@APP.route('/set_value', methods=["POST"])
def set_value():
    """
    update a boolean drain value for a given env/direction/interval
    """
    direction = request.args.get('direction')
    env = request.args.get('env')
    interval = request.args.get('interval')
    value = str2bool(request.args.get('value', type=str))
    struct = get_struct(env)
    struct[f'tf_{interval}'][direction] = value if value is not None else False
    set_struct(env, struct)
    return Response(status=200)

@APP.route('/get_envs', methods=["GET"])
def get_envs():
    """
    Return a list of supported envs
    """
    return ENVS

@APP.route('/get_env', methods=["GET"])
def get_env():
    """
    get structure for a given environment
    """
    env = request.args.get('env')
    if env not in ENVS:
        return Response(response=f'Invalid Environment: {env}', status=400)
    struct = get_struct(env)
    return struct

@APP.route('/get_value', methods=["GET"])
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

    try:
        action = 'close' if direction = 'close' else 'open'
        top_result = struct[f'top_{action}']
    except KeyError:
        top_result = False
    result = struct[f'tf_{interval}'][direction] or top_result
    print(f"You provided {direction},{interval}, {env}.......{result}")

    return {'result':result}

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
