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

    # temp table we will use to filter out incomplete balance records
    drop = "drop table if exists `temp_table`"

    # There needs to be 3 records for each date representing 3 exchanges
    clean = ("create table temp_table  as SELECT ctime FROM balance where coin='TOTALS' "
             "GROUP BY ctime HAVING count(*) <3")

    delete1 = "delete from balance where ctime in (select * from temp_table)"

    # Update balance summary and clean out old balance records
    update = ("insert into balance_summary (select ctime, sum(usd) as usd from balance where "
              "coin='TOTALS' and left(ctime,10) != CURDATE() group by ctime")

    delete2 = "delete from balance where left(ctime,10) != CURDATE()"

    # Generate OHLC data
    query = ("select c1.ctime as closeTime, (SELECT c2.usd FROM balance_summary c2 WHERE "
             "c2.ctime = MIN(c1.ctime)) AS open, MAX(c1.usd) AS high, MIN(c1.usd) AS low, "
             "(SELECT c2.usd FROM balance_summary c2 WHERE c2.ctime = MAX(c1.ctime)) "
             "AS close FROM balance_summary c1  GROUP BY left(ctime,10) "
             "ORDER BY c1.ctime ASC")

    # Run queries
    mysql.fetch_sql_data(drop)
    mysql.fetch_sql_data(clean)
    mysql.fetch_sql_data(delete1)
    mysql.fetch_sql_data(drop)
    mysql.fetch_sql_data(update)
    mysql.fetch_sql_data(delete2)
    results = mysql.fetch_sql_data(query)

    # Convert results into pandas dataframe using header as column title
    dframe = pandas.DataFrame(results, columns=results.pop(0))
    dframe['closeTime'] = pandas.to_datetime(dframe['closeTime']).values.astype(numpy.int64) \
            // 10**6

    # Generate graph
    graph = Graph(False, pair="Balance", interval='1d', volume=False)
    graph.insert_data(dframe)
    graph.create_graph('/data/graphs')

if __name__ == '__main__':
    main()
