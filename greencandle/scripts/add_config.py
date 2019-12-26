#!/usr/bin/env python
#pylint: disable=consider-iterating-dictionary

"""
Add active config to configstore
"""

import sys
import subprocess
import shlex

from ..lib import config
config.create_config()

def get_result(command):
    """
    Run command using subprocess and return stdout in UTF-8
    """
    output = subprocess.check_output(shlex.split(command))
    return output.decode('UTF-8').strip()

def main():
    """
    Main function
    """

    try:
        env = sys.argv[1]
    except IndexError:
        sys.exit("Usage: {0} <env>".format(sys.argv[0]))

    secret = ['email_from', 'email_to', 'email_password', 'push_host', 'push_channel',
              'binance_api_key', 'binance_api_secret', 'coinbase_api_key', 'coinbase_api_secret']

    for section in config.REQUIRED_CONFIG.keys():
        for key, value in getattr(config, section).items():
            if key not in secret:
                command = "configstore package get {env} {key}".format(env=env, key=key)
                result = get_result(command)
                if result != value:
                    command = 'configstore package set {env} {key} "{value}"'.format(env=env,
                                                                                     key=key,
                                                                                     value=value)
                get_result(command)

if __name__ == '__main__':
    main()
