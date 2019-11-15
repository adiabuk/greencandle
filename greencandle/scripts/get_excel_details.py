#!/usr/bin/env python
"""
Get total sum of perc profit from each xlsx file in current directory
"""

import glob
import pandas as pd



def main():
    """
    Main function
    """
    files = glob.glob('*.xlsx')
    for file in files:
        dframe = pd.read_excel(file, sheet_name='profit-pair')
        print(dframe["pair"].to_string(header=False).split()[-1],
              dframe["perc"].to_string(header=False).split()[-1])

if __name__ == '__main__':
    main()
