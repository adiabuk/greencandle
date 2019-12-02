#!/usr/bin/env python

"""
Analize and collate data from Excep reports
"""

import sys
import glob
import pandas as pd


def main():
    """Main function"""

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Send alerts if docker containers are down")
        sys.exit(0)

    files = glob.glob('*.xlsx')

    for file in files:
        dframe = pd.read_excel(file, sheet_name='profit-pair')
        print(dframe["pair"].to_string(header=False).split()[-1],
              dframe["perc"].to_string(header=False).split()[-1])
if __name__ == '__main__':
    main()
