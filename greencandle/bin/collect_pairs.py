#!/usr/bin/env python
#pylint: disable=wrong-import-position
"""
Import pairs from remote db
"""
from greencandle.lib import config
from greencandle.lib.common import arg_decorator
config.create_config()
from greencandle.lib.mysql import Mysql

@arg_decorator
def main():
    """
    Import pairs from remote db
    """
    dbase = Mysql()
    dbase2 = Mysql(host='10.8.0.101', port=3308)


    # fetch from remote db
    pairs = dbase2.fetch_sql_data('select pair from tmp_pairs', header=False)
    pairs = [x[0] for x in pairs]
    pstr = (' '.join('("{}"),'.format(item) for item in pairs)).rstrip(',')

    # insert into local db
    dbase.run_sql_statement('create table if not exists tmp_pairs (pair varchar(30))')
    dbase.delete_table_contents('tmp_pairs')
    dbase.run_sql_statement('insert into tmp_pairs (pair) VALUES {}'.format(pstr))

if __name__ == '__main__':
    main()
