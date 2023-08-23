
"""Test lint of python files"""

import unittest
import json
from glob import glob

class TestJson(unittest.TestCase):
    """Test Lint Unittest"""

    def test_json(self):
        """
        test json
        """
        for filename in glob('config/env/**/*.json', recursive=True):
            print(f"Testing {filename}")
            with open(filename) as handle:
                json.load(handle)
