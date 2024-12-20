#pylint: disable=no-member,no-name-in-module
"""
Follow log files and alert on Error and high occurances of errors
"""
from datetime import datetime, timedelta
import re
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

def check_last_hour_err():
    """
    Check number of errors logged in last hour and report to nagios via NSCA
    """
    env = config.main.base_env
    logfile = open(f"/var/log/gc_{env}.log", 'r').readlines()
    err_count= 0
    warn_count = 0
    for line in logfile:
        string = " ".join(line.split()[:3])
        fmt = "%b %d %H:%M:%S"
        current = datetime.strptime(string, fmt).replace(datetime.now().year)
        last_hour_date_time = datetime.now() - timedelta(hours = 1)

        if current > last_hour_date_time and any(status in line for status in ['CRIT', 'ERR',
                                                                               'Traceback']):
            err_count += 1
        if current > last_hour_date_time and "WARN" in line:
            warn_count += 1

    log_warn = {"prod": 50,
                "data": 50,
                "stag": 500,
                "test": 1000}
    perf = f"|warn={warn_count};;;;err_count={err_count}"
    if err_count > 50:
        status = 2
        msg = "CRITICAL"
        text = (f'{msg}: {err_count} ERROR/CRITICAL entries in {env} logfile, warn:'
                f'{warn_count}{perf}')
    elif warn_count > log_warn[env]:
        status = 1
        msg = "WARNING"
        text = f'{msg}: {warn_count} WARN entries in {env} logfile, err:crit: {err_count}{perf}'
    else:
        status = 0
        msg = "OK"
        text = (f'{msg}: No major issues in {env} logfile, warn:{warn_count}, err/crit:'
                f'{err_count}{perf}')

    send_nsca(status=status, host_name="jenkins", service_name=f"critical_logs_{env}",
              text_output=text, remote_host='nagios.amrox.loc')


def check_last_hour_occ():
    """
    Check number of strategy entries logged in last hour and report to nagios via NSCA
    """
    env = config.main.base_env
    logfile = open(f"/var/log/gc_{env}.log", 'r').readlines()
    count= 0
    for line in logfile:
        string = " ".join(line.split()[:3])
        fmt = "%b %d %H:%M:%S"
        current = datetime.strptime(string, fmt).replace(datetime.now().year)
        last_hour_date_time = datetime.now() - timedelta(hours = 1)
        regexes = [".*long17.*alert", ".*short17.*alert"]
        combined = "(" + ")|(".join(regexes) + ")"

        if current > last_hour_date_time and re.match(combined, line):
            count += 1

    perf = f"|count={count};;;;"

    if count > 50:
        status = 2
        msg = "CRITICAL"
        text = f'{msg}: {count} long17/short17 entries in {env} logfile, count:{count}{perf}'
    elif count > 20:
        status = 1
        msg = "WARNING"
        text = f'{msg}: {count} long17/short17 entries in {env} logfile, count:{count}{perf}'
    else:
        status = 0
        msg = "OK"
        text = f'{msg}: {count} long17/short17 entries in {env} logfile, count:{count}{perf}'

    send_nsca(status=status, host_name="data", service_name=f"strategy17_count_{env}",
              text_output=text, remote_host='nagios.amrox.loc')

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
    scheduler.add_job(func=check_last_hour_err, trigger="interval", minutes=5)
    if env == 'data':
        scheduler.add_job(func=check_last_hour_occ, trigger="interval", minutes=5)
    scheduler.start()
    watch_log()

if __name__ == '__main__':
    main()
