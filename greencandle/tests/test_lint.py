
"""Test lint of python files"""

import unittest
from pathlib import Path
from pylint.lint import Run

class TestLint(unittest.TestCase):
    """Test Lint Unittest"""

    def test_lint(self):
        """
        test lint
        """
        for filename in Path('greencandle').rglob('*.py'):
            file = open(str(filename))
            count = len(file.readlines())
            file.close()
            if 'test' not in str(filename) and count > 5:
                results = Run([str(filename)], do_exit=False)
                try:
                    print(filename)
                    score = results.linter.stats['global_note']
                    self.assertGreaterEqual(score, 9.5)
                except KeyError:
                    pass
