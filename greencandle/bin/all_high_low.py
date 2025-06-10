#!/usr/local/bin/python -u
#pylint: disable=no-member
"""
Extract high/low data from all pairs and send to prometheus
Usage: all_high_low <interval>
"""

import json
import sys
import os
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator
from greencandle.lib.logger import get_logger
from greencandle.lib.objects import AttributeDict
from greencandle.lib import config
from greencandle.lib.web import push_prom_data

@arg_decorator
def main():
    """
    main func
    """
    name = os.path.basename(__file__).split('.')[0]
    logger = get_logger(name)

    config.create_config()
    redis = Redis()
    pairs = config.main.pairs.split()
    interval=sys.argv[1]

    count = {'up': 0, 'down': 0, 'range':0}
    for pair in pairs:
        item = redis.get_intervals(pair, interval)[-1]
        res = AttributeDict(json.loads(redis.get_item('{}:{}'.format(pair, interval),
            item).decode()))
        if res.HL_30[0] >= res.HL_60[0] and res.HL_30[1] >= res.HL_60[1]:
            count['up'] += 1
        elif res.HL_30[0] <= res.HL_60[0] and res.HL_30[1] <= res.HL_60[1]:
            count['down'] += 1
        else:
            count['range'] += 1
    for key, val in count.items():
        name = f'data_HL_{key}_{interval}'
        push_prom_data(name, val)
    logger.info('')
    logger.info("Output: %s %s",interval, count)

if __name__ == "__main__":
    main()
