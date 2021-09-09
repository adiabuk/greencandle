
"""Test scripts"""

import unittest
import glob
import os

class TestScripts(unittest.TestCase):
    """Test executables included in package"""

    def test_python_scripts(self):
        """
        test python executables in bin dir
        """
        entrypoints = []
        files = glob.glob('greencandle/bin/[!_]*.py')
        for filename in files:
            path = filename.rstrip('.py').replace('/', '.')
            name = path.split('.')[-1]
            string = "{0}={1}:main".format(name, path)
            entrypoints.append(string)
            print("Running {}".format(name))
            result = os.system("{} --help >/dev/null 2>&1".format(name))
            self.assertEqual(result, 0)
        return entrypoints
