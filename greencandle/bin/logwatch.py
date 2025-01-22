#pylint: disable=no-member,no-name-in-module,consider-using-with
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
from greencandle.lib.web import push_prom_data

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
    logfile = reversed(open(f"/var/log/gc_{env}.log", 'r', encoding="utf-8").readlines())
    err_count= 0
    warn_count = 0
    for line in logfile:
        string = " ".join(line.split()[:3])
        fmt = "%b %d %H:%M:%S"
        current = datetime.strptime(string, fmt).replace(datetime.now().year)
        last_hour_date_time = datetime.now() - timedelta(hours = 1)

        if current > last_hour_date_time:
            if any(status in line for status in ['CRIT', 'ERR', 'Traceback'] and '1m' not in line):
                err_count += 1
            if "WARN" in line and '1m' not in line:
                warn_count += 1
        else:
            break

    log_warn = {"prod": 50,
                "per": 50,
                "data": 50,
                "stag": 500,
                "test": 1000}
    perf = f"|warn={warn_count} err={err_count};;;;"
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
    host = "data" if env == "data" else "jenkins"
    send_nsca(status=status, host_name=host, service_name=f"critical_logs_{env}",
              text_output=text, remote_host='nagios.amrox.loc')

def check_last_hour_occ():
    """
    Check number of strategy entries logged in last hour and report to nagios via NSCA
    """
    env = config.main.base_env
    logfile = reversed(open(f"/var/log/gc_{env}.log", 'r', encoding="utf-8").readlines())
    low_count=0
    high_count=0
    long_cross=0
    short_cross=0
    for line in logfile:
        string = " ".join(line.split()[:3])
        fmt = "%b %d %H:%M:%S"
        current = datetime.strptime(string, fmt).replace(datetime.now().year)
        last_hour_date_time = datetime.now() - timedelta(hours = 1)
        low_match="(.*long17.*alert)"
        high_match="(.*short17.*alert)"
        long_xover="(.*long.*xover.*1h)"
        short_xover="(.*short.*xover.*1h)"

        if current > last_hour_date_time:
            if re.match(low_match, line):
                low_count += 1
            if  re.match(high_match, line):
                high_count += 1
            if re.match(long_xover, line):
                long_cross += 1
            if re.match(short_xover, line):
                short_cross += 1
        else:
            break

    levels_warn=20
    levels_crit=50
    xover_warn=10
    xover_crit=20
    levels_perf = f"|low={low_count} high={high_count};{levels_warn};{levels_crit};;"
    levels_text = f"stragegy17 levels low:{low_count},high:{high_count}"
    if low_count > levels_crit or high_count > levels_crit:
        status = 2
        msg = "CRITICAL"
    elif low_count > levels_warn or high_count > levels_warn:
        status = 1
        msg = "WARNING"
    else:
        status = 0
        msg = "OK"
    text = f'{msg}: {levels_text}{levels_perf}'

    send_nsca(status=status, host_name="data", service_name=f"strategy17_count_{env}",
              text_output=text, remote_host='nagios.amrox.loc')

    push_prom_data('strategy17_up_1h', high_count)
    push_prom_data('strategy17_down_1h', low_count)

    xover_perf = f"|long={long_cross} short={short_cross};{xover_warn};{xover_crit};;"
    xover_text = f"xover long:{long_cross},short:{short_cross}"
    if long_cross > xover_crit or short_cross > xover_crit:
        status = 2
        msg = "CRITICAL"
    elif long_cross > xover_warn or short_cross > xover_warn:
        status = 1
        msg = "WARNING"
    else:
        status = 0
        msg = "OK"
    xover_full_text = f'{msg}: {xover_text}{xover_perf}'


    send_nsca(status=status, host_name="data", service_name=f"xover_count_{env}",
              text_output=xover_full_text, remote_host='nagios.amrox.loc')

def watch_log():
    """
    watch logs for exceptions
    """
    env = config.main.base_env
    client = docker.from_env()
    with open(f"/var/log/gc_{env}.log", "r", encoding="utf-8") as logfile:
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
