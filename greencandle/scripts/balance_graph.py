#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member

"""
Create OHLC graph using daily balance
"""

import sys
import numpy
import pandas
from greencandle.lib import config
config.create_config()
from greencandle.lib.mysql import Mysql

from greencandle.lib.graph import Graph


def main():
    """
    Main function
    """
    mysql = Mysql()

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Create OHLC graph using daily balance")
        sys.exit(0)

    query = """
    select
           left(ctime,10) as closeTime,
           (select usd group by left(ctime,10) order by ctime asc limit 1) as open,
           max(usd) as high,
           min(usd) as low,
           (select usd group by left(ctime,10) order by ctime desc limit 1) as close
            from(
    select ctime, sum(usd) as usd from balance where coin='TOTALS' group by ctime
    ) as t group by left(ctime,10);
    """
    results = mysql.fetch_sql_data(query)
    dframe = pandas.DataFrame(results, columns=results.pop(0))
    dframe['closeTime'] = pandas.to_datetime(dframe['closeTime']).values.astype(numpy.int64) \
            // 10**6
    graph = Graph(False, pair="Balance", interval='1d', volume=False)
    graph.insert_data(dframe)
    graph.create_graph('.')

if __name__ == '__main__':
    main()
