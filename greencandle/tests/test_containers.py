#!/usr/bin/env python
"""
Test docker containers
"""
import unittest
import subprocess
import yaml
from greencandle.lib.common import get_worker_containers, get_short_name, list_to_dict

ENVS = ('per', 'prod', 'stag', 'test')

class TestContainers(unittest.TestCase):
    """
    Test containers
    """

    def test_short_name(self):
        """
        Ensure containers have a shortname set in dc config
        """
        for env in ENVS:
            containers = get_worker_containers(env)

            with open('/srv/greencandle/install/docker-compose_{}.yml'.format(env), 'r') as stream:
                output = yaml.safe_load(stream)
                #keys = list(output['services'].keys())

            for cont in containers:
                if cont.endswith('data') or cont.endswith('router'):
                    continue
                config_env = list_to_dict(output['services'][cont]['environment'],
                                          delimiter='=', reverse=False)['CONFIG_ENV']

                command = ('configstore package get --basedir /srv/greencandle/config {} '
                           'trade_direction'.format(config_env))

                result = subprocess.Popen(command.split(),
                                          stdout=subprocess.PIPE).stdout.read().split()[0].decode()
                short = get_short_name(cont, env, result)
                print(cont, short)
                self.assertNotEqual(short, 'xxx')

