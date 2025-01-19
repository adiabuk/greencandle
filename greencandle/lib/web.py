#pylint: disable=too-few-public-methods
"""
Libraries for use in API modules
"""
import requests

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
