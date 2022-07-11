#!/usr/bin/env python
#pylint: disable=no-else-return
"""
Flask based web proxy
"""
from flask import Flask, request, Response
import requests
from greencandle.lib.common import arg_decorator

APP = Flask(__name__, static_url_path='/not_static')

@APP.route('/<path:path>', methods=['GET', 'POST', 'DELETE'])
@APP.route('/', defaults={'path': ''}, methods=['GET'])
@APP.route('/<path:path>', methods=['GET'])
@APP.route('/static', methods=['GET'])
@APP.route('/filesystem', methods=['GET'])
@APP.route('/browse', methods=['GET'])
@APP.route('/open', methods=['GET'])
def proxy(path="/"):
    """
    capture all proxy routes
    """
    site_name = "http://filesystem:6000"
    path = '/' if path == 'filesystem' else path
    if request.method == 'GET':
        resp = requests.get(f'{site_name}/{path}')
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding',
                            'connection']
        headers = [(name, value) for (name, value) in  resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    elif request.method == 'POST':
        resp = requests.post(f'{site_name}{path}', json=request.get_json())
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding',
                            'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    elif request.method == 'DELETE':
        resp = requests.delete(f'{site_name}{path}').content
        response = Response(resp.content, resp.status_code, headers)
        return response
    return None

@arg_decorator
def main():
    """proxy request to another host"""
    APP.run(debug=False, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
