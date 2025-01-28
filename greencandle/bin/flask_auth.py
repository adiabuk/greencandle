#!/usr/bin/env python
#pylint: disable=no-member
"""
Module for encrypting and decrypting credentials with fernet lib
"""

import sys
import getpass
from cryptography.fernet import Fernet
from greencandle.lib import config
from greencandle.lib.common import arg_decorator

@arg_decorator
def main():
    """
    encrypt and decrypt credentials for flask api modules
    format should take the form of "user:pass"
    Usage: auth [encrypt|decrypt]
    """
    config.create_config()
    key = config.web.auth_key
    fernet = Fernet(key)

    if sys.argv[1] == "encrypt":
        username = input('username: ').strip()
        password = getpass.getpass()
        password2 = getpass.getpass("again: ")
        if not password == password2:
            print("Passwords don't match")
            sys.exit(2)
        message = f"{username}:{password}"
        encoded = fernet.encrypt(message.encode())
        print(encoded)

    elif sys.argv[1] == "decrypt":
        auth_raw = config.web.flask_auth.encode()
        user, passw = fernet.decrypt(auth_raw).decode().split(':')
        print(user, passw)

if __name__ == '__main__':
    main()
