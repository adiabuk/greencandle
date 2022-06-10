
from flask import request, redirect, abort, Response
from flask_login import UserMixin, login_user, logout_user

# silly user model
class User(UserMixin):

    def __init__(self, username):

        self.id = username
        self.password = USERS_DB[username]

    def __repr__(self):
        return "%s/%s" % (self.id, self.password)

    def is_active(self):
        return True

#users database (used dictionary just as an example)
USERS_DB = {'user1':'pass1',
            'user2': 'pass2',
            'user3' : 'pass3'
            }

def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (username, password) in USERS_DB.items():
            login_user(User(username))
            return redirect(request.args.get("next"))
        else:
            return abort(401)
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')

def logout():
    logout_user()
    return Response('<p>Logged out</p>')

def page_not_found(_):
    return Response('<p>Login failed</p>')


def load_user(userid):
    return User(userid)
