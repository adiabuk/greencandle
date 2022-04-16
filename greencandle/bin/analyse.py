#!/usr/bin/env python

"""
Analise and collate data from Excel reports
"""

import glob
import pandas as pd
from greencandle.lib.common import arg_decorator

@arg_decorator
def main():
    """Analyse available xlsx reports and print perc/par for each file"""

    files = glob.glob('*.xlsx')

    for file in files:
        dframe = pd.read_excel(file, sheet_name='profit-pair')
        print(dframe["pair"].to_string(header=False).split()[-1],
              dframe["perc"].to_string(header=False).split()[-1])
if __name__ == '__main__':
    main()
