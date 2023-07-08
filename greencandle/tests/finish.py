# pylint: disable=wrong-import-position

"""
Aggregate test results, and perform git checks

"""

import os
import sys

BASE_DIR = os.getcwd().split('netgenius', 1)[0]+'netgenius'
sys.path.append(BASE_DIR)

from greencandle.tests.print_format import  print_status_line

def finish_test(results=None):
    """ Start tests """
    total = 0
    print("\n\n")
    print("=" * 74)
    print("TEST RESULTS SUMMARY")
    print("=" * 74)
    # process results
    for name, result in results:
        status_code = 0 if result == 100 else 1
        text = "{0}: {1:.2f}% pass rate".format(name, result)
        print_status_line(text, status_code)
        total += result
    total /= len(results)
    print("=" * 74)
    total_text = "Total: {0:.2f}%".format(total)
    total_code = 0 if total == 100 else 1

    print_status_line(total_text, total_code)
    update_results(int(total))

    return total_code

def update_results(result):
    """ Adding new test results. """
    # Get current GIT COMMIT SHA to include in results

    # Write Results to log file to be read by git hook
    with open('results.log', 'w') as results_file:
        if  result != 100:  # not all passed
            results = "FAILED"
        else:  # everything OK
            results = "OK"
        print(results)
        results_file.write(results)

if __name__ == '__main__':
    finish_test()
    print("This module is a library and should not be called directly.")
    print("Use run_tests.py instead from the root directory")
    sys.exit(1)
