#!/usr/bin/env python
#pylint: disable=no-member
"""
missing tpsl alert for nagios
"""
from send_nsca3 import send_nsca
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.lib import config
from greencandle.lib.common import arg_decorator


@arg_decorator
def main():
    """
    Find open trades that don't have an associated tpsl in redis
    and forward to nagios/nsca
    """
    config.create_config()
    redis = Redis()
    dbase = Mysql()

    trades = dbase.get_open_trades()
    no_tpsl = []

    for item in trades:
        _, interval, pair, name, _, direction, _ = item
        current_take = redis.get_on_entry(pair, 'take_profit_perc', name=name,
                                          interval=interval, direction=direction)
        if current_take == 0:
            no_tpsl.append(pair)

    if len(no_tpsl) > 0:
        msg = "Some pairs have no tpsl in redis: " + " ".join(no_tpsl)
        status = 2
    else:
        msg = "all pairs have tpsl"
        status = 0
    env = config.main.base_env
    send_nsca(status=status, host_name='eaglenest', service_name=f'{env}_tpsl', text_output=msg,
              remote_host='nagios.amrox.loc')


if __name__ == '__main__':
    main()
