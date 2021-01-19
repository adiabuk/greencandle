#!/usr/bin/env python
#pylint: disable=wrong-import-position
"""
Generate drawup scatter graph using perc/drawup data in mysql
"""

import sys
import plotly.graph_objs as go
import plotly.offline as py
import pandas as pd
from greencandle.lib import config
config.create_config()
from greencandle.lib.mysql import Mysql

def usage():
    """
    print command usage
    """
    sys.stderr.write("Usage: {0} <interval> <filename>\n".format(sys.argv[0]))

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        usage()
        sys.exit(0)
    elif len(sys.argv) < 3:
        usage()
        sys.exit(1)
    interval = sys.argv[1]
    dbase = Mysql(interval=interval)
    data = dbase.fetch_sql_data("select perc, drawup_perc from profit", header=False)
    dframe = pd.DataFrame.from_records(data, columns=("perc", "drawup"))


    fig = go.Figure(data=[go.Scatter(x=dframe['drawup'], y=dframe['perc'],
                                     name="events",
                                     mode='markers')])
    filename = sys.argv[2]
    fig.update_xaxes(title_text='drawup')
    fig.update_yaxes(title_text='perc')
    fig.update_layout(title_text="Drawup Scatter -{}".format(filename))

    py.plot(fig, filename=filename, auto_open=False)


if __name__ == '__main__':
    main()
