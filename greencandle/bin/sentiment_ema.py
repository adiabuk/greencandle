#!/usr/bin/env python
#pylint: disable=no-member
"""
Get number of pairs above and below EMA_150
"""
import sys
import json
from datetime import datetime
import numpy as np
from send_nsca3 import send_nsca
from greencandle.lib import config
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator

def get_max(up, down):
    """
    determine if general trend is up or down
    depending on size of lists containing the 2 trends
    """
    listsnames = ['up', 'down']
    lists = [up,down]
    most= listsnames[np.argmax([len(l) for l in lists])]
    return most

@arg_decorator
def main():
    """
    Determine of the overall trend of available pairs is up or down
    depending on whether the majority of pairs are above or below the 150 EMA
    Send to nagios via NSCA
    """
    config.create_config()
    redis = Redis()

    up = []
    down = []
    interval = sys.argv[1] if len(sys.argv) > 1 else '1h'
    for pair in config.main.pairs.split():
        try:
            item = redis.get_intervals(pair, interval)[-1]
            x = json.loads(redis.get_item(f'{pair}:{interval}', item).decode())


            if float(x['ohlc']['close']) > x['EMA_150']:
                up.append(pair)
            else:
                down.append(pair)

        except Exception as e:
            print("bad %s",e, pair)

    dt_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f'/data/ema_stats/ema_{interval}_{dt_stamp}.json'
    max_direction = get_max(up, down)
    up_perc=round(len(up)/len(config.main.pairs.split())*100,2)
    down_perc=round(len(down)/len(config.main.pairs.split())*100,2)
    data = {'max': max_direction, 'up_perc': up_perc, 'down_perc': down_perc,
            'date': dt_stamp, 'up_list': up, 'down_list': down}

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    details = f"up_perc: {up_perc}%, down_perc: {down_perc}%"

    if up_perc > 60 or down_perc > 60:
        status=2
        msg="CRITICAL"
    elif up_perc > 30 or down_perc > 30:
        status=1
        msg="WARNING"
    else:
        status=0
        msg="OK"

    text = f"{msg}: Direction is {max_direction}: {details}"
    send_nsca(status=status, host_name='data', service_name='EMA_150',
              text_output=text, remote_host='nagios.amrox.loc')
    print(text)
    sys.exit(status)
