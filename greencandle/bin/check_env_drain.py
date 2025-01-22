#!/usr/bin/env python
#pylint: disable=no-member,global-statement
"""
Check for enabled drain in given environment
"""
import sys
import requests
from send_nsca3 import send_nsca
from greencandle.lib import config
from greencandle.lib.common import arg_decorator
from greencandle.lib.logger import get_logger

TRUE_VALUES = 0

def traverse_and_count(struct):
    """
    Recursive function to traverse nested dict and get count of number of "True" boolean values
    Function needs a global var defined outside of scope to maintain count as we traverse
    """
    global TRUE_VALUES
    for value in struct.values():
        if isinstance(value, dict):
            traverse_and_count(value)
        else:
            if isinstance(value, bool) and value:
                TRUE_VALUES+=1
    return TRUE_VALUES

@arg_decorator
def main():
    """
    Get drain config for given environment from config env
    and iterate through returned dictionary - count number of enabled drains (for each combination
    of direction and intervals), and send alert on total count via NCSA.
    This should be run periodically in each environment using cron
    """

    logger = get_logger(__name__)
    config.create_config()
    env = config.main.base_env
    a = requests.get(f'http://config.amrox.loc/drain/get_env?env={env}', timeout=10)
    count = traverse_and_count(a.json())

    if count > 3:
        status = 2
        msg = "CRITICAL"
    elif count > 0:
        status = 1
        msg = "WARNING"
    elif count == 0:
        status = 0
        msg = "OK"
    else:
        status = 3
        msg = "UNKNOWN"
    host = "data" if env == "data" else "jenkins"
    text = f"{msg}: {count} drain entries found for {env} env"
    send_nsca(status=status, host_name=host, service_name=f"{env}_drain",
              text_output=text, remote_host="nagios.amrox.loc")
    logger.info(text)
    sys.exit(status)

if __name__ == '__main__':
    main()
