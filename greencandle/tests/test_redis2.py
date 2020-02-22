import unittest
from . import test_redis
MODULES=["test_redis"]
def start_test():
    """ run unit tests """
    test_suite = []
    for module in MODULES:
        test_suite.extend(unittest.TestLoader().loadTestsFromModule(
            globals()[module]))

    test_suite = unittest.suite.TestSuite(test_suite)
    runner = unittest.TextTestRunner()
    result = runner.run(test_suite)
    total = result.testsRun
    failed = len(result.errors) + len(result.failures)
    perc = 100 - (100*float(failed)/total)
    return perc

