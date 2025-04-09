
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
            path = filename.split('.')[0].replace('/', '.')
            name = path.split('.')[-1]
            string = f"{name}={path}:main"
            entrypoints.append(string)
            print(f"Running {name}")
            result = check_call([name, '--help'], stdout=DEVNULL, stderr=STDOUT)
            self.assertEqual(result, 0)
        return entrypoints
