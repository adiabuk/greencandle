#!/usr/bin/env python
#pylint: disable=no-member
"""
Push version details to prometheus
"""
import os
from prometheus_client import CollectorRegistry, push_to_gateway, Info
from greencandle.lib.common import arg_decorator
from greencandle.lib import config

@arg_decorator
def main():
    """
    Get version and build date from envronment
    and push to prometheus
    """
    config.create_config()
    env = config.main.base_env
    version=os.environ['VERSION']
    build_date = os.environ['BUILD_DATE']

    registry = CollectorRegistry()
    i = Info(f'gc_version_{env}', 'version details', registry=registry)
    i.info({'version': version, 'build_date': build_date })

    push_to_gateway('jenkins:9091', job=f'{env}_metrics', registry=registry)

if __name__ == "__main__":
    main()
