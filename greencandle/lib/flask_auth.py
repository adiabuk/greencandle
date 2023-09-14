#!/usr/bin/env python
#pylint: disable=invalid-overridden-method,invalid-name,no-member

"""
Libraries for adding auth to all Flask api modules
"""
from flask import request, redirect, abort, render_template
from flask_login import UserMixin, login_user, logout_user
from cryptography.fernet import Fernet
from greencandle.lib import config
config.create_config()
auth = config.web.flask_auth.encode()
#key = Fernet.generate_key()
key = config.web.auth_key.encode()
fernet = Fernet(key)
#https://www.geeksforgeeks.org/how-to-encrypt-and-decrypt-strings-in-python/
user, passw = fernet.decrypt(auth).decode().split(':')
USERS_DB = {user:passw}

class User(UserMixin):
    """
    User object
    """

    def __init__(self, username):
        self.id = username
        self.password = USERS_DB[username]

    def __repr__(self):
        return f"{self.id}/{self.password}"

    def is_active(self):
        """if logged in"""
        return True

def login():
    """login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (username, password) in USERS_DB.items():
            login_user(User(username))
            return redirect(request.args.get("next"))
        return abort(401)
    return render_template('login.html')

def logout():
    """logout page"""
    logout_user()
    return render_template('logout.html')

def page_not_found(_):
    """404 page"""
    return render_template('failed.html', message="Login failed")

def load_user(userid):
    """load user"""
    return User(userid)
