#!/usr/bin/env python
#pylint: disable=no-else-return,invalid-overridden-method,invalid-name,no-self-use
"""
Libraries for adding auth to all Flask api modules
"""

from flask import request, redirect, abort, render_template
from flask_login import UserMixin, login_user, logout_user

# silly user model
class User(UserMixin):
    """
    User object
    """

    def __init__(self, username):
        self.id = username
        self.password = USERS_DB[username]

    def __repr__(self):
        return "%s/%s" % (self.id, self.password)

    def is_active(self):
        """if logged in"""
        return True

#users database (used dictionary just as an example)
USERS_DB = {'user1':'pass1',
            'user2': 'pass2',
            'user3' : 'pass3'
            }

def login():
    """login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (username, password) in USERS_DB.items():
            login_user(User(username))
            return redirect(request.args.get("next"))
        else:
            return abort(401)
    else:
        return render_template('login.html')

def logout():
    """logout page"""
    logout_user()
    return render_template('logout.html')

def page_not_found(_):
    """404 page"""
    return render_template('failed.html')

def load_user(userid):
    """load user"""
    return User(userid)
