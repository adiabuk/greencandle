#!/usr/bin/env python
#pylint: disable=protected-access

"""
Get values from config file
"""

import sys

from configparser import ConfigParser


def get_config(section):
    """
    Read config file and return required config
    Args:
        section: string section of configfile
    Return
        dict of config parameters/values in given section
    """
    parser = ConfigParser()
    parser.read("/etc/greencandle.ini")
    return parser._sections[section]


if __name__ == "__main__":
    print(get_config(sys.argv[1]))
