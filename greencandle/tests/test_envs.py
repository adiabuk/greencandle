#pylint: disable=wrong-import-position,no-member,protected-access
"""Test environments"""

import os
import glob
import unittest

class TestEnvs(unittest.TestCase):
    """
    Test all environments in docker compose files
    """

    def test_environments(self):
        """
        Scrape environments from CONFIG_ENV vars in docker compose file and test
        """
        environments = []
        files = glob.glob('/srv/greencandle/install/docker-compose*')
        for file in files:
            with open(file, 'r') as compose_file:
                lines = compose_file.readlines()
                for line in lines:
                    if "CONFIG_ENV" in line:
                        environments.append(line.split('=')[-1].rstrip())

        for env in environments:
            exit_code = os.system('configstore package get {} pairs'.format(env))
            self.assertEqual(exit_code, 0)
