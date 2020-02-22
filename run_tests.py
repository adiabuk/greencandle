#!/usr/bin/env python
# pylint: disable=relative-import,unused-import

"""
Main test module
All tests should be run from here
"""

import argparse
import sys

from greencandle.tests.print_format import SuppressStdoutStderr
from greencandle.tests.test_finish import start_test as test_finish
from greencandle.tests.__init__ import __all__
#from lib.tests.test_lint import start_test as test_lint
#from lib.tests.test_api import start_test as test_api
#from lib.tests.test_journey import start_test as test_journey
#from lib.tests.test_finish import start_test as test_finish
#from lib.tests.test_unit import start_test as test_unit
#from lib.tests.test_selenium import start_test as test_selenium

# Tuple of tuples
# (name, module)
TESTS = __all__
#TESTS = [  # main tests - run by default
#    ("API", "test_api"),
#    ("Journey", "test_journey"),
#    ("Unit", "test_unit"),
#    ("Lint", "test_lint"),
#    ]
TESTS = [("redis", "test_redis2")]
from greencandle.tests.test_redis2 import start_test as test_redis2

print(TESTS)

# Optional Tests - only run with the --run-optional flag
OPT_TESTS = [
    (None, None),  # HACK: Need more than one item to construct tuple of tuple
    ("GUI", "test_selenium")
    ]

def run_tests(tests_to_run='all', run_optional=False):
    """ Run all available tests and return results in a tuple """

    results = []

    # Only include optional tests if we have specified --run_optional
    # or specified an optional test by name
    if tests_to_run == 'all' and not run_optional:
        tests = TESTS
    else:
        OPT_TESTS.remove((None, None))
        tests = TESTS + OPT_TESTS

    # Construct list of what to run
    run_lst = [x for x in tests if x[0] == tests_to_run or tests_to_run == 'all']

    # Run each module and append to list as tuple, with the name
    for name, module in run_lst:
        print(name, module)
        results.append((name, globals()[module]()))

    return results

def print_list():
    """ Print avilable tests with bullet points """
    print("Available tests:")
    for item in TESTS:
        print(" * ", item[0])
    print()
    print("Optional tests:")
    for item in OPT_TESTS:
        if item[0]:
            print(" * ", item[0])

def main():
    """ Main function """

    parser = argparse.ArgumentParser('Global Testing module')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-v', '--verbose', action='store_true', required=False,
                       help='Display all test output')
    group.add_argument('-s', '--summary', action='store_true', required=False,
                       help='Display only results summary')
    group.add_argument('-l', '--list_tests', action='store_true', default=False,
                       required=False, help='list available tests')
    parser.add_argument('-t', '--test', dest="test", type=str, default="all",
                        help='run a specific test', required=False)
    parser.add_argument('-r', '--run_optional', action='store_true',
                        default=False, help='run option tests')

    args = parser.parse_args()
    if not (any(args.test == x[0] for x in TESTS + OPT_TESTS) or args.test == 'all'):
        print("Invalid test")
        print_list()
        sys.exit(1)
    elif args.list_tests:
        print_list()
        sys.exit(0)

    if args.summary:
        # supress stdout for all tests if module called with --summary
        print("Running tests...")
        with SuppressStdoutStderr():
            results = run_tests(args.test)
    else:
        # run tests with full output
        results = run_tests(args.test, args.run_optional)

    # Run finish_tests module to collate results
    # and perform checks
    exit_code = test_finish(results)


    if args.summary:
        print("Details suppressed.  Run with --verbose to see full output\n")

    sys.exit(exit_code)

if __name__ == '__main__':
    main()
