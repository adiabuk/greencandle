#pylint: disable=no-member
"""
Flask module to provide web interface for tailing /var/log/greencandle.log
"""

import os
import time
from flask import Flask, render_template
from flask_login import LoginManager, login_required
import sh
import setproctitle
from greencandle.lib.common import arg_decorator
from greencandle.lib.flask_auth import load_user, login as loginx, logout as logoutx

APP = Flask(__name__, template_folder="/var/ww/html", static_url_path='/',
            static_folder='/var/www/html')
LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.init_app(APP)
LOGIN_MANAGER.login_view = "login"
APP.config['SECRET_KEY'] = os.environ['SECRET_KEY'] if 'SECRET_KEY' in os.environ else \
        os.urandom(12).hex()
load_user = LOGIN_MANAGER.user_loader(load_user)
login = APP.route("/login", methods=["GET", "POST"])(loginx)
logout = APP.route("/logout", methods=["GET", "POST"])(logoutx)

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
        while True:
            try:
                for line in sh.tail("-f", '/var/log/greencandle.log', _iter=True):
                    yield line
                    time.sleep(1)
            except sh.ErrorReturnCode_1:
                yield None

    return APP.response_class(generate(), mimetype='text/plain')

@arg_decorator
def main():
    """Web interface for current host gc logs"""
    setproctitle.setproctitle("logtailer")
    APP.run(debug=False, host='0.0.0.0', port=2000, threaded=True)

if __name__ == '__main__':
    main()
