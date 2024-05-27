#pylint: disable=no-member,no-name-in-module
"""
Follow log files and alert on Error and high occurances of errors
"""
from datetime import datetime, timedelta
import time
import os
import docker
from apscheduler.schedulers.background import BackgroundScheduler
from send_nsca3 import send_nsca
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

def check_last_hour():
    """
    Check number of errors logged in last hour and report to nagios via NSCA
    """
    env = config.main.base_env
    logfile = open(f"/var/log/gc_{env}.log", 'r').readlines()
    count = 0
    for line in logfile:
        string = " ".join(line.split()[:3])
        fmt = "%b %d %H:%M:%S"
        current = datetime.strptime(string, fmt).replace(datetime.now().year)
        last_hour_date_time = datetime.now() - timedelta(hours = 1)

        if current > last_hour_date_time and 'CRITICAL' in line:
            count += 1
    if count > 200:
        status = 2
        msg = "CRITICAL"
    elif count > 100:
        status = 1
        msg = "WARNING"
    else:
        status = 0
        msg = "OK"

    send_nsca(status=status, host_name="jenkins1", service_name=f"critical_logs_{env}",
              text_output=f"{msg}: {count} critical entries in {env} logfile",
              remote_host='nagios.amrox.loc')

    print(count)

def watch_log():
    """
    watch logs for exceptions
    """
    env = config.main.base_env
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


@arg_decorator
def main():
    """
    Checks on gc log files for patterns and number of occurances
    Ensure /var/log/gc_<env>.log is shared with docker container

    Usage: logwatch
    """
    config.create_config()
    env = config.main.base_env
    setproctitle(f"{env}-logwatch")
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_last_hour, trigger="interval", minutes=5)
    scheduler.start()
    watch_log()

if __name__ == '__main__':
    main()
