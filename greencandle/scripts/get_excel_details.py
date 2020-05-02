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
    if len(sys.argv) != 2 or sys.argv[1] not in ("annual", "monthly"):
        sys.stderr.write("Usage: {} <annual|monthly>\n".format(sys.argv[0]))
        sys.exit(1)
    else:
        output = sys.argv[1]

    for file in files:
        if output == "annual":
            dframe = pd.read_excel(file, sheet_name='profit-pair')
            print(dframe["pair"].to_string(header=False).split()[-1],
                  dframe["perc"].to_string(header=False).split()[-1])
        elif output == "monthly":
            dframe = pd.read_excel(file, sheet_name='monthly')
            print(dframe)

if __name__ == '__main__':
    main()
