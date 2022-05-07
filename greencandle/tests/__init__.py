#!/usr/bin/env python
"""
returns list of available tests
"""

from os.path import dirname, basename, isfile, join
import glob

MODULES = glob.glob(join(dirname(__file__), "test*.py"))
__all__ = [(basename(f).replace('test_', '')[:-3], basename(f)[:-3])
           for f in MODULES if isfile(f) and not f.endswith('__init__.py')]
