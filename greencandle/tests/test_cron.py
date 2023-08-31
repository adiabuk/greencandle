#pylint: disable=wrong-import-position,no-member,protected-access,too-many-locals
"""Test Cron"""

import unittest
import json
import os
import yaml
from greencandle.bin.api_dashboard import get_pairs, list_to_dict


ENVS = ('per', 'prod', 'stag', 'test', 'alarm')
class TestCron(unittest.TestCase):
    """
    Test all assocs in docker-compose and config
    """

    def test_cron_files(self):
        """
        Ensure all envs in router configs exist
        """

        for env in ENVS:
            os.system("sudo configstore package process_templates {} /tmp".format(env))
            print("Testing", env)
            os.system("crontab /tmp/gc-cron")
            print("Done testing", env)

