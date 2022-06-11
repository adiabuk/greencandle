#!/usr/bin/env python
#pylint: disable=invalid-name
"""
Flask module to provide web interface for tailing /var/log/syslog
"""

import time
from flask import Flask, render_template
from flask_login import LoginManager, login_required
from greencandle.lib.common import arg_decorator
from greencandle.lib.flask_auth import load_user, login as loginx, logout as logoutx

APP = Flask(__name__, template_folder="/etc/gcapi", static_url_path='/',
            static_folder='/etc/gcapi')
LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.init_app(APP)
LOGIN_MANAGER.login_view = "login"
APP.config['SECRET_KEY'] = 'shit'
load_user = LOGIN_MANAGER.user_loader(load_user)
login = APP.route("/login", methods=["GET", "POST"])(loginx)
login = APP.route("/logout", methods=["GET", "POST"])(logoutx)

@APP.route('/')
@login_required
def index():
    """default route"""
    return render_template('log.html')

@APP.route('/stream')
@login_required
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
