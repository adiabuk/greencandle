#pylint: disable=unnecessary-pass

"""
Unittest file for testing health of docker containers by starting them up individually and checking
for functionality, health status, and dependencies
"""

import unittest

from greencandle.lib.logger import get_logger
from .unittests import make_docker_case
LOGGER = get_logger(__name__)

class TestCron(make_docker_case('cron', checks=["crontab -l"])):
    """Test cron docker instance"""
    pass

if __name__ == '__main__':
    unittest.main()
