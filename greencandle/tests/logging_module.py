#!/usr/bin/env python

"""
Helper functions to print for test output and other logging
"""

# use print function instead of built in as it's thread-safe
from __future__ import print_function
import os

ROWS, COLUMNS = os.popen('stty size', 'r').read().split()


def print_status_line(strings, exit_code):
    """
    print given string along with colored OK / FAILED message on the right
    depending on given status code, 0=SUCCESS, other=FAILED
    """
    # Colors used to print status block
    bold = '\033[1m'
    green = '\033[92m'
    red = '\033[31m'
    end = '\033[0m'

    # populate OK/FAILED string with color in bold
    status = green + "OK" if exit_code == 0 else red + 'FAILED'
    status_block = (bold + '[ ' + '  ' + status + '  ' +  end + bold
                    + ' ]' + end)

    offset = len(strings)
    line_new = strings +":" + status_block.rjust(int(COLUMNS)-offset)
    print(line_new + '\n')
    return exit_code
