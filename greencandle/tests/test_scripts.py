
"""Test scripts"""

import unittest
import glob
from subprocess import DEVNULL, STDOUT, check_call

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
            result = check_call(['ls', '-l', '/usr/local/bin/' + name], stdout=DEVNULL, stderr=STDOUT)
            check_call([name, '--help'], stdout=DEVNULL, stderr=STDOUT)
            self.assertEqual(result, 0)
        return entrypoints
