#!/usr/bin/env python
"""
Generate scatter graph for short/long profit over time
from mysql data
"""

import datetime
import pandas as pd
import plotly.express as px
import plotly.offline as py
from greencandle.lib.common import arg_decorator
from greencandle.lib import config
from greencandle.lib.mysql import Mysql

@arg_decorator
def main():
    """
    Create profit scatter chart

    Usage: profitable_graph
    """

    config.create_config()
    dbase = Mysql()
    data = dbase.fetch_sql_data("select perc, close_time, direction from profit", header=False)

    dframe = pd.DataFrame.from_records(data, columns=("perc", "close_time", "direction"))

    fig = px.scatter(dframe, x="close_time", y="perc", color="direction")
    now = datetime.datetime.now()
    date = now.strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"profitable_{date}.html"
    fig.update_xaxes(title_text="profitable")
    fig.update_yaxes(title_text='perc')
    fig.update_layout(title_text="Profitable Scatter")

    py.plot(fig, filename=filename, auto_open=False)
    print(f"Done creating profitable chart as {filename}")


if __name__ == '__main__':
    main()
