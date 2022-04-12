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
    @staticmethod
    def test_assocs():
        """
        Scrape environments from CONFIG_ENV vars in docker compose file and test
        """
        envs = (('per', 'PROD'), ('prod', 'PROD'), ('stag', 'STAG'))
        for env, host in envs:
            os.environ['HOST'] = host
            names = get_pairs()[-1]
            rev_names = {v: k for k, v in names.items()}
            with open('/srv/greencandle/config/template/router_config_{}.json'.format(env),
                      'r') as json_file:
                router_config = json.load(json_file)

            with open("/srv/greencandle/install/docker-compose_{}.yml"
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
