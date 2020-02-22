#!/usr/bin/env python
# pylint: disable=relative-import,unused-import

"""
Main test module
All tests should be run from here
"""

import argparse
import sys
import unittest
from greencandle.tests.print_format import SuppressStdoutStderr
from greencandle.tests.finish import start_test as test_finish
from greencandle.tests.__init__ import __all__
#for i in __all__:
#    globals()[i[1]] = __import__('greencandle.tests.'+i[1])

from greencandle.tests import test_redis, test_run, test_mysql, test_lint, test_scripts, test_docker

# Tuple of tuples
# (name, module)
TESTS = __all__
print(TESTS)
#from greencandle.tests.redis2 import start_test as redis2
#from greencandle.tests.redis2 import start_test


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
        print(globals())
        #results.append((name, dglobals()[module]()))
        results.append((name, start_test(module)))

    print(results)
    print('xxx')
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

def start_test(module):
    """ run unit tests """
    test_suite = []
    test_suite.extend(unittest.TestLoader().loadTestsFromModule(
            globals()[module]))

    test_suite = unittest.suite.TestSuite(test_suite)
    runner = unittest.TextTestRunner()
    result = runner.run(test_suite)
    total = result.testsRun
    failed = len(result.errors) + len(result.failures)
    perc = 100 - (100*float(failed)/total)
    return perc

if __name__ == '__main__':
    main()
