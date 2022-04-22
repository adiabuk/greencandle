#pylint: disable=wrong-import-position
"""
Follow log files and alert on Error
"""
import time
import os
from greencandle.lib import config
config.create_config()
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import arg_decorator

def follow(thefile):
    """
    Generator function that yields new lines in a file
    """
    # seek the end of the file
    thefile.seek(0, os.SEEK_END)

    # start infinite loop
    while True:
        # read last line of file
        line = thefile.readline()        # sleep if file hasn't been updated
        if not line:
            time.sleep(0.1)
            continue

        yield line

@arg_decorator
def main():
    """
    Tail syslog of current host and alert on unhandled traceback events
    Ensure /var/log/syslog is shared with docker container

    Usage: logwatch
    """

    logfile = open("/var/log/syslog", "r")
    loglines = follow(logfile)    # iterate over the generator
    for line in loglines:
        if "Traceback" in line:
            send_slack_message("alerts", "String found in logfile: \"Traceback\"")

if __name__ == '__main__':
    main()
