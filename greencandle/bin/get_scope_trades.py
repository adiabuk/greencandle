#!/usr/bin/env python
#pylint: disable=no-member
"""
Small command line tool to show pairs of open trades in current scope
"""
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import arg_decorator
from greencandle.lib import config


@arg_decorator
def main():
    """
    Small command line tool to show pairs of open trades in current scope
    """
    dbase = Mysql()
    config.create_config()
    results = dbase.fetch_sql_data(f'select pair from trades where name="{config.main.name}" '
                                   f'and direction="{config.main.trade_direction}" and close_price '
                                   'is null', header=False)

    pairs = [item for sublist in results for item in sublist]
    for pair in pairs:
        print(pair.strip())

if __name__ == '__main__':
    main()
