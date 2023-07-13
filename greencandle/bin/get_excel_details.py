#!/usr/bin/env python
"""
Get total sum of perc profit from each xlsx file in current directory
Monthly and Annually
"""

import os
import sys
import glob
import pandas as pd
from xlrd.biffh import XLRDError
from greencandle.lib.common import arg_decorator

@arg_decorator
def main():
    """
    Extract data from Excel reports
    Choose from annual, monthly, or factor (profit factor)
    Results will be outputted to stdout

    Usage: get_excel_details <annual|monthly|factor>
    """
    files = glob.glob('*.xlsx')
    if len(sys.argv) != 2 or sys.argv[1] not in ("annual", "monthly", "factor", "--help"):
        sys.stderr.write(f"Usage: {sys.argv[0]} <annual|monthly|factor>\n")
        sys.exit(1)

    output = sys.argv[1]
    year = os.getcwd().split('/')[-1]
    strategy = os.getcwd().split('/')[-2]
    if output == "annual":
        # print titles
        print("pair perc hours factor max_month year strategy prof count prof_perc")
    for file in files:
        try:
            if output == "annual":

                dframe = pd.read_excel(file, sheet_name='profit-pair')
                pair = dframe["pair"].to_string(header=False).split()[-1]
                perc = dframe["perc"].to_string(header=False).split()[-1]

                dframe = pd.read_excel(file, sheet_name='hours-pair')
                hours = dframe["hours"].to_string(header=False).split()[-1]

                dframe = pd.read_excel(file, sheet_name='profit-factor')
                factor = dframe["profit_factor"].to_string(header=False).split()[-1]

                dframe = pd.read_excel(file, sheet_name='perc-month')
                sorted_dframe = dframe.sort_values('perc', ascending=False)['month']
                highest_month = sorted_dframe.iloc[0]

                dframe = pd.read_excel(file, sheet_name='trades')
                total = len(dframe['perc'])
                more = len(dframe[(dframe['perc'] > 0)])
                perc_prof = (more/total) * 100

                print(pair, perc, hours, factor, highest_month, year, strategy, more, total,
                      perc_prof)
            elif output == "monthly":
                dframe = pd.read_excel(file, sheet_name='perc-month')
                print(dframe)
            elif output == "factor":
                dframe = pd.read_excel(file, sheet_name='profit-factor')
                print(file, dframe["profit_factor"].to_string(header=False).split()[-1])
        except (IndexError, XLRDError):
            continue


if __name__ == '__main__':
    main()
