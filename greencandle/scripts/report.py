#!/usr/bin/env python
#pylint: disable=wrong-import-position

"""
Create Excel Spreadsheet with results and analysis of trades
"""

import sys
import openpyxl
from greencandle.lib.mysql import Mysql
from greencandle.lib import config
config.create_config(test=True)

def main():
    """
    main function
    """

    filename = sys.argv[1]
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.get_sheet_by_name('Sheet'))

    mysql = Mysql(test=True, interval='1h')
    queries = {"weekly": "select perc, pair, week(sell_time) as week from profit",
               "monthly": "select perc, pair, month(sell_time) as month from profit",
               "average-day": "select pair, hour(timediff(sell_time,buy_time)) as hours from \
                       trades where sell_time != '0000-00-00 00:00:00' group by pair;",
               "perc-month": "select pair, sum(perc)  as perc, month(sell_time) as month from \
                        profit where sell_time != '0000-00-00 00:00:00'  group by pair, month \
                        order by month,perc;",
               "profit-pair": "select pair, sum(perc) as perc from profit where \
                        sell_time != '0000-00-00 00:00:00' group by pair;",
               "hours-pair": "select pair, sum(hour(timediff(sell_time,buy_time))) \
                        as hours from trades where sell_time \
                        != '0000-00-00 00:00:00' group by pair"}
    for name, query in queries.items():
        result = mysql.fetch_sql_data(query)
        workbook.create_sheet(title=name)
        sheet = workbook.get_sheet_by_name(name)
        for row_no, row in enumerate(result):
            for col_no, col in enumerate(row):
                sheet.cell(row=row_no+1, column=col_no+1).value = col
        workbook.save(filename)

if __name__ == "__main__":
    main()
