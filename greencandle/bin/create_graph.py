#!/usr/bin/env python
#pylint: disable=no-member

"""
Standalone script for generating graphs from data in redis
"""

import argparse
import argcomplete

from greencandle.lib import config
from greencandle.lib.graph import parse_args

def main():
    """Main function"""
    config.create_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--all_pairs", action="store_true", required=False, default=False)
    parser.add_argument("-p", "--pair", required=False)
    parser.add_argument("-i", "--interval", required=False)
    parser.add_argument("-t", "--test", action="store_true", default=False, required=False)
    parser.add_argument("-o", "--output_dir", required=True)
    parser.add_argument("-m", "--thumbnails", required=False, action="store_true", default=False)
    argcomplete.autocomplete(parser)

    parse_args(**vars(parser.parse_args()))

if __name__ == '__main__':
    main()
