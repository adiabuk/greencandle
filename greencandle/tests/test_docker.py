#pylint: disable=unnecessary-pass

"""
Unittest file for testing health of docker containers by starting them up individually and checking
for functionality, health status, and dependencies
"""

import unittest

from greencandle.lib.logger import get_logger
from .unittests import make_docker_case
LOGGER = get_logger(__name__)

class TestMysql(make_docker_case('mysql-unit', checks=["echo 'SELECT version();'| "
                                                       "mysql --protocol=tcp -uroot -ppassword"]
                                 )):
    """Test mysql docker instance"""
    pass

class TestRedis(make_docker_case('redis-unit', checks=["redis-cli ping"])):
    """Test redis docker instance"""
    pass

class TestApi(make_docker_case('api', checks=["nc -z 127.1 20000"])):
    """Test api docker instance"""
    pass

class TestCron(make_docker_case('cron', checks=[""])):
    """Test cron docker instance"""
    pass

if __name__ == '__main__':
    unittest.main()
