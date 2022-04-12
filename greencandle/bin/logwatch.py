#pylint: disable=wrong-import-position
"""
Follow log files and alert on Error
"""
import sys
import time
import os
from greencandle.lib import config
config.create_config()
from greencandle.lib.alerts import send_slack_message

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

def main():
    """
    Main func
    """
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Usage: {} <pair>".format(sys.argv[0]))
        sys.exit(0)
    logfile = open("/var/log/syslog", "r")
    loglines = follow(logfile)    # iterate over the generator
    for line in loglines:
        if "Traceback" in line:
            send_slack_message("notifications", "String found in logfile")

if __name__ == '__main__':
    main()
