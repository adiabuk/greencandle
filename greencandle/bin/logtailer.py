#!/usr/bin/env python

"""
Flask module to provide web interface for tailing /var/log/syslog
"""

import time
from flask import Flask, render_template
from greencandle.lib.common import arg_decorator

APP = Flask(__name__, template_folder=".")

@APP.route('/')
def index():
    """default route"""
    return render_template('index.html')

@APP.route('/stream')
def stream():
    """
    stream path
    """
    def generate():
        """ Generator for yielding log file contents """
        with open('/var/log/syslog') as log_file:
            while True:
                yield log_file.read()
                time.sleep(1)

    return APP.response_class(generate(), mimetype='text/plain')

@arg_decorator
def main():
    """Web interface for current host syslog"""
    APP.run(debug=True, host='0.0.0.0', port=2222, threaded=True)

if __name__ == '__main__':
    main()
