#!/usr/bin/env python
"""
Generate drawup scatter graph using perc & drawup/drawdown
data in mysql
"""

import sys
import pandas as pd
import plotly.graph_objs as go
import plotly.offline as py
from greencandle.lib.common import arg_decorator
from greencandle.lib import config
from greencandle.lib.mysql import Mysql

config.create_config()

def usage():
    """
    print command usage
    """
    sys.stderr.write(f"Usage: {sys.argv[0]} <interval> <filename> up|down [table]\n")
    sys.exit(1)

@arg_decorator
def main():
    """
    Create drawdown and drawup scatter chart

    Usage: create_drawchart <interval> <filename> up|down
    """

    if len(sys.argv) < 4:
        usage()
    interval = sys.argv[1]

    dbase = Mysql(interval=interval)

    if sys.argv[3] not in ("up", "down"):
        usage()
    try:
        table = sys.argv[4]
    except IndexError:
        table = "profit"

    field = "draw" + sys.argv[3]

    data = dbase.fetch_sql_data(f"select perc, {field}_perc from {table}", header=False)
    dframe = pd.DataFrame.from_records(data, columns=("perc", field))

    fig = go.Figure(data=[go.Scatter(x=dframe[field], y=dframe['perc'],
                                     name="events",
                                     mode='markers')])
    filename = sys.argv[2]
    fig.update_xaxes(title_text=field)
    fig.update_yaxes(title_text='perc')
    fig.update_layout(title_text=f"{field} Scatter -{filename}")

    py.plot(fig, filename=filename, auto_open=False)
    print(f"Done creating {field} chart as {filename}")


if __name__ == '__main__':
    main()
