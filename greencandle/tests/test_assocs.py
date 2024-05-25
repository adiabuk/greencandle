#pylint: disable=wrong-import-position,no-member,protected-access,too-many-locals
"""Test environments"""

import unittest
import json
import os
import yaml
from greencandle.bin.api_dashboard import list_to_dict


ENVS = ('per', 'prod', 'stag', 'test', 'alarm')
ENVS = ('prod','per')
class TestAssocs(unittest.TestCase):
    """
    Test all assocs in docker-compose and config
    """

    def test_router_config(self):
        """
        Ensure all envs in router configs exist
        """

        for env in ENVS:
            os.system("sudo configstore package process_templates {} /tmp".format(env))
            with open('/tmp/router_config.json', 'r') as json_file:
                router_config = json.load(json_file)
            with open("install/docker-compose_{}.yml"
                      .format(env), "r") as stream:
                try:
                    output = (yaml.safe_load(stream))
                except yaml.YAMLError as exc:
                    print(exc)
            print("Testing", env)
            links_list = output['services']['{}-be-api-router'.format(env)]['links']
            service_list = [item.split(":")[-1] for item in links_list]

            router_config = [v for k, v in router_config.items()]
            router_config_flat_list = [item for sublist in router_config for item in sublist]

            for item in router_config_flat_list:
                if env != 'alarm' and item != 'alert':  # alert container only in test env
                    # alert uses hosts file in non-test envs
                    self.assertIn(item, service_list)
        print("Done testing", env)

    @staticmethod
    def test_assocs():
        """
        Scrape environments from CONFIG_ENV vars in docker compose file and test
        """
        for env in ENVS:
            print("processing env {}".format(env))
            os.system("sudo configstore package process_templates {} /tmp".format(env))
            with open('/tmp/router_config.json', 'r') as json_file:
                router_config = json.load(json_file)

            with open("install/docker-compose_{}.yml"
                      .format(env), "r") as stream:
                try:
                    output = (yaml.safe_load(stream))
                except yaml.YAMLError as exc:
                    print(exc)
            links_list = output['services']['{}-be-api-router'.format(env)]['links']
            links_dict = list_to_dict(links_list, str_filter='-be-')
            for _, short_name in router_config.items():
                for item in short_name:
                    name = item.split(':')[0]
                    print(f"processing item: {item} in {env}")
                    if env != 'alarm' and name == 'alert':
                        continue
                    try:
                        container = links_dict[name]
                    except KeyError:
                        print("Issue with {} in {}".format(name, env))
                        raise

                    if not container.startswith('{}-be-'.format(env)) and 'alert' not in container:
                        continue
