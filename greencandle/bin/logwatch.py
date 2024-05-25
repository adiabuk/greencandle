#pylint: disable=no-member,no-name-in-module
"""
Follow log files and alert on Error
"""
import time
import os
import docker
from setproctitle import setproctitle
from greencandle.lib import config
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
    Tail gc logs on current host and alert on unhandled traceback events
    Ensure /var/log/greencandle.log is shared with docker container

    Usage: logwatch
    """
    config.create_config()
    env = config.main.base_env
    setproctitle(f"{env}-logwatch")
    client = docker.from_env()
    with open(f"/var/log/gc_{env}.log", "r") as logfile:
        loglines = follow(logfile)    # iterate over the generator
        for line in loglines:
            if "Traceback" in line:
                container_id = line.split()[4]
                match = container_id[0:container_id.find('[')]
                try:
                    name = client.containers.get(match).name
                except docker.errors.NotFound:
                    name = f"unknown - {container_id}"
                if name.startswith(env) or container_id.startswith(env):
                    send_slack_message("alerts", f"Unhandled exception found in {name} container")

if __name__ == '__main__':
    main()
