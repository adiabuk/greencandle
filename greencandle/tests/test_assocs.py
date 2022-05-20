#pylint: disable=wrong-import-position,no-member,protected-access,too-many-locals
"""Test environments"""

import unittest
import json
import os
import yaml
from greencandle.bin.api_dashboard import get_pairs, list_to_dict


class TestAssocs(unittest.TestCase):
    """
    Test all assocs in docker-compose and config
    """

    def test_router_config(self):
        """
        Ensure all envs in router configs exist
        """

        envs = (('per', 'PROD'), ('prod', 'PROD'), ('stag', 'STAG'))
        for env, host in envs:
            os.system("configstore package process_templates {} /tmp".format(env))
            with open('/tmp/router_config.json', 'r') as json_file:
                router_config = json.load(json_file)
            with open("install/docker-compose_{}.yml"
                      .format(host.lower()), "r") as stream:
                try:
                    output = (yaml.safe_load(stream))
                except yaml.YAMLError as exc:
                    print(exc)
            print("Testing " + env)
            links_list = output['services']['{}-be-api-router'.format(env)]['links']
            service_list = [item.split(":")[-1] for item in links_list]

            router_config = [v for k, v in router_config.items()]
            router_config_flat_list = [item for sublist in router_config for item in sublist]

            for item in router_config_flat_list:
                if env != 'stag' and item != 'alert':
                    # alert uses hosts file in non-stag envs
                    self.assertIn(item, service_list)




    @staticmethod
    def test_assocs():
        """
        Scrape environments from CONFIG_ENV vars in docker compose file and test
        """
        envs = (('per', 'PROD'), ('prod', 'PROD'), ('stag', 'STAG'))
        for env, host in envs:
            os.system("configstore package process_templates {} /tmp".format(env))
            os.environ['HOST'] = host
            names = get_pairs()[-1]
            rev_names = {v: k for k, v in names.items()}
            with open('/tmp/router_config.json', 'r') as json_file:
                router_config = json.load(json_file)

            with open("install/docker-compose_{}.yml"
                      .format(host.lower()), "r") as stream:
                try:
                    output = (yaml.safe_load(stream))
                except yaml.YAMLError as exc:
                    print(exc)

        links_list = output['services']['{}-be-api-router'.format(env)]['links']
        links_dict = list_to_dict(links_list)
        for _, short_name in router_config.items():
            for item in short_name:
                name = item.split(':')[0]
                container = links_dict[name]
                if container.startswith('{}-be-'.format(env)) and 'alert' not in container:
                    actual_name = container.replace('-be', '')  # strip off container type
                else:
                    continue
                _ = rev_names[actual_name]
