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

    dbase.run_sql_statement('drop table if exists tmp_pairs')
    dbase.run_sql_statement('create table tmp_pairs as SELECT distinct(pair) from '
                            'profitable_by_name_pair where perc_profitable > 60 '
                            'and name like "%bbpercst2%"')

if __name__ == '__main__':
    main()
