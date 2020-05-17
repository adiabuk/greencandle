#!/usr/bin/env python
"""
Get total sum of perc profit from each xlsx file in current directory
Monthly and Annually
"""

import sys
import glob
import pandas as pd



def main():
    """
    Main function
    """
    files = glob.glob('*.xlsx')
    if len(sys.argv) != 2 or sys.argv[1] not in ("annual", "monthly", "factor", "--help"):
        sys.stderr.write("Usage: {} <annual|monthly|factor>\n".format(sys.argv[0]))
        sys.exit(1)
    elif sys.argv[1] == '--help':
        sys.stderr.write("Extract data from Excel reports\n")
        sys.stderr.write("Usage: {} <annual|monthly>\n".format(sys.argv[0]))
        sys.exit(0)

    output = sys.argv[1]

    for file in files:
        try:
            if output == "annual":
                dframe = pd.read_excel(file, sheet_name='profit-pair')
                print(dframe["pair"].to_string(header=False).split()[-1],
                      dframe["perc"].to_string(header=False).split()[-1])
            elif output == "monthly":
                dframe = pd.read_excel(file, sheet_name='perc-month')
                print(dframe)
            elif output =="factor":
                dframe = pd.read_excel(file, sheet_name='profit-factor')
                print(file, dframe["profit_factor"].to_string(header=False).split()[-1])
        except:
            continue


if __name__ == '__main__':
    main()
