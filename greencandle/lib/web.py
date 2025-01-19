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

def get_drain(env, interval, direction):
    """
    Get drain status from api for given env,interval,direction
    """
    url = (f'http://config.amrox.loc/drain/get_value?env={env}&direction={direction}'
          f'&interval={interval}')
    req = requests.get(url, timeout=2)
    return req.json()['result']
