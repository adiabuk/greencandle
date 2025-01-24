#pylint: disable=too-few-public-methods,no-member,global-statement
"""
Libraries for use in API modules
"""
from time import time
import requests
from greencandle.lib import config
config.create_config()
TRUE_VALUES = 0

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

def push_prom_data(metric_name, value, job_name=None):
    """
    Push metric to pushgateway for prometheus
    """
    value = 0 if (value is None or value == '') else value
    job_name = f"{config.main.base_env}_metrics" if not job_name else job_name
    headers = {'X-Requested-With': 'gc requests', 'Content-type': 'text/xml'}
    url = f"http://jenkins:9091/metrics/job/{job_name}"
    data = f"{metric_name} {value}\n"
    requests.post(url, headers=headers, data=data, timeout=10)

def count_struct(struct):
    """
    Get number of True values in a dict structure
    Reset global var to zero each time we called so it's not using module level aggregation
    """
    global TRUE_VALUES
    TRUE_VALUES = 0
    def traverse(struct):
        """
        Recursive function to traverse nested dict and get count of number of "True" boolean values
        Function needs a global var defined outside of scope to maintain count as we traverse
        """
        global TRUE_VALUES
        for value in struct.values():
            if isinstance(value, dict):
                traverse(value)
            else:
                if isinstance(value, bool) and value:
                    TRUE_VALUES+=1
    traverse(struct)
    return TRUE_VALUES

def find_paths(nested_dict, value, prepath=()):
    """
    Use generator to yield paths in nested dict
    having a given value
    """
    for k, v in nested_dict.items():
        path = prepath + (k,)
        if v == value: # found value
            yield path
        elif hasattr(v, 'items'): # v is a dict
            yield from find_paths(v, value, path)

def decorator_timer(some_function):
    """
    Decorator to send function execution time to prometheus
    """
    def wrapper(*args, **kwargs):
        t1 = time()
        result = some_function(*args, **kwargs)
        end = time()-t1
        metric_name = f'gc_time_{some_function.__name__}_{config.main.name}'.replace('-','_')
        push_prom_data(metric_name=metric_name,
                       value=str(end), job_name=f'gc_{config.main.base_env}_metrics')
        return result
    return wrapper
