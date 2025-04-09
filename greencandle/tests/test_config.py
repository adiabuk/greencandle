#pylint: disable=wrong-import-position,no-member,protected-access
"""Test environments"""

import os
import unittest
import yaml
from greencandle.lib import config

class TestConfig(unittest.TestCase):
    """
    Test all assocs in docker-compose and config
    """

    def test_config(self):
        """
        Scrape environments from CONFIG_ENV vars in docker compose file and test
        """
        base_envs = ["prod", "stag", "data", "unit", "test"]
        final_envs = set()
        failed = set()
        for env in base_envs:
            with open(f"install/docker-compose_{env}.yml", 'r', encoding='utf-8') as stream:
                output = yaml.safe_load(stream)
            for _, val in output['services'].items():
                try:
                    var = val['environment'][0].split("=")
                    if var[0] == "CONFIG_ENV":
                        final_envs.add(var[1])
                except KeyError:
                    pass
        for env in final_envs:
            print(env)
            os.system(f"configstore package process_templates {env} /etc")
            try:
                config.create_config()
            except AttributeError:
                failed.add(env)
        if failed:
            self.fail(f"The following envs have missing config: {failed}")

    def test_config2(self):
        """
        Run configstore pakcage test and ensure it exits with code 0
        """
        exit_code = os.system("configstore package test")
        self.assertEqual(exit_code, 0)
