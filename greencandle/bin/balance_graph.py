#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member

"""
Create OHLC graph using daily balance
"""

import numpy
import pandas
from greencandle.lib.common import arg_decorator
from greencandle.lib import config
config.create_config()
from greencandle.lib.mysql import Mysql
from greencandle.lib.graph import Graph

@arg_decorator
def main():
    """
    Create OHLC graph using balance data for BTC and USDT
    Will create graph in current directory based on data in DB

    Usage: balance_graph
    """
    mysql = Mysql()

    # temp table we will use to filter out incomplete balance records
    drop = "drop table if exists `temp_table`"

    # There needs to be 4 records for each date representing 3 exchanges
    clean = ("create table temp_table  as SELECT ctime FROM balance where coin='TOTALS' "
             "GROUP BY ctime HAVING count(*) <4")

    delete1 = "delete from balance where ctime in (select * from temp_table)"

    # Update balance summary and clean out old balance records
    update = ("insert into balance_summary (select ctime, sum(usd) as usd, sum(btc) as btc "
              "from balance where coin='TOTALS' and left(ctime,10) != CURDATE() group by ctime)")

    delete2 = "delete from balance where left(ctime,10) != CURDATE()"

    # Generate OHLC data
    query = ("select c1.ctime as openTime, (SELECT c2.{0} FROM balance_summary c2 WHERE "
             "c2.ctime = MIN(c1.ctime) limit 1) AS open, MAX(c1.{0}) AS high, MIN(c1.{0}) AS low, "
             "(SELECT c2.{0} FROM balance_summary c2 WHERE c2.ctime = MAX(c1.ctime) limit 1) "
             "AS close FROM balance_summary c1  GROUP BY left(ctime,10) "
             "ORDER BY c1.ctime ASC")
    btc_query = query.format("btc")
    usd_query = query.format("usd")

    # Run queries
    mysql.run_sql_statement(drop)
    mysql.run_sql_statement(clean)
    mysql.run_sql_statement(delete1)
    mysql.run_sql_statement(drop)
    mysql.run_sql_statement(update)
    usd_results = mysql.fetch_sql_data(usd_query)
    btc_results = mysql.fetch_sql_data(btc_query)
    mysql.run_sql_statement(delete2)

    # Convert results into pandas dataframe using header as column title
    usd_dframe = pandas.DataFrame(usd_results, columns=usd_results.pop(0))
    usd_dframe['openTime'] = pandas.to_datetime(usd_dframe['openTime']) \
            .values.astype(numpy.int64) / 10**6

    btc_dframe = pandas.DataFrame(btc_results, columns=btc_results.pop(0))
    btc_dframe['openTime'] = pandas.to_datetime(btc_dframe['openTime']) \
            .values.astype(numpy.int64) / 10**6

    # Generate graph
    graph = Graph(False, pair="Balance-usd", interval='1d', volume=False)
    graph.insert_data(usd_dframe)
    graph.create_graph('/data/graphs')

    graph = Graph(False, pair="Balance-btc", interval='1d', volume=False)
    graph.insert_data(btc_dframe)
    graph.create_graph('/data/graphs')
if __name__ == '__main__':
    main()
