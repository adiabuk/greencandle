#pylint: disable=too-few-public-methods,no-member
"""
Libraries for use in API modules
"""
import requests
from greencandle.lib import config

class PrefixMiddleware():
    """
    add url prefix
    """

    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):

        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        start_response('404', [('Content-Type', 'text/plain')])
        return ["This url does not belong to the app.".encode()]

def set_drain(**kwargs):
    """
    enable disable drain value for a given env/interval/direction
    Mandatory args: env, value, direction
    Optional args: interval (without direction global value will be set/unset
    """

    url = 'http://config.amrox.loc/drain/set_value'
    requests.post(url, json=kwargs, timeout=2)

def get_drain(env, interval, direction):
    """
    Get drain status from api for given env,interval,direction
    """
    url = (f'http://config.amrox.loc/drain/get_value?env={env}&direction={direction}'
          f'&interval={interval}')
    req = requests.get(url, timeout=2)
    return req.json()['result']

def get_drain_env(env):
    """
    get drain json for entire given environment
    """
    url = f'http://config.amrox.loc/drain/get_env?env={env}'
    req = requests.get(url, timeout=2)
    return req.json()

def push_prom_data(metric_name, value):
    """
    Push metric to pushgateway for prometheus
    """
    value = 0 if (value is None or value == '') else value
    config.create_config()
    job_name = f"{config.main.base_env}_metrics"
    headers = {'X-Requested-With': 'gc requests', 'Content-type': 'text/xml'}
    url = f"http://jenkins:9091/metrics/job/{job_name}"
    data = f"{metric_name} {value}\n"
    requests.post(url, headers=headers, data=data, timeout=10)
