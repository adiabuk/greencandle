#!/usr/bin/env python
#pylint: disable=wrong-import-position
"""
Get list of profitable pairs
"""
from greencandle.lib import config
from greencandle.lib.common import arg_decorator
config.create_config()
from greencandle.lib.mysql import Mysql

@arg_decorator
def main():
    """
    Populate table of profitable pairs for given strategy
    """
    dbase = Mysql()

    dbase.delete_table_contents('tmp_pairs')
    dbase.run_sql_statement('insert into tmp_pairs (pair) SELECT distinct(pair) from '
                            'profitable_by_name_pair where net_per_trade > 0 '
                            'and name like "%bbpercst3%"')

if __name__ == '__main__':
    main()
