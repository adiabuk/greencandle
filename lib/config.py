#!/usr/bin/env python

import sys

from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.ini')

def get_config(section):
    return parser._sections[section]


if __name__ == "__main__":
    print(get_config(sys.argv[1]))
