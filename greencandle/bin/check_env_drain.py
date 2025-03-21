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
from greencandle.lib.web import count_struct

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
    a = requests.get(f'http://config.amrox.loc/drain/get_env?env={env}', timeout=20)
    count = count_struct(a.json())

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
    host = "datavault" if env == "data" else "eaglenest"
    text = f"{msg}: {count} drain entries found for {env} env"
    send_nsca(status=status, host_name=host, service_name=f"{env}_drain",
              text_output=text, remote_host="nagios.amrox.loc")
    logger.info(text)
    sys.exit(status)

if __name__ == '__main__':
    main()
