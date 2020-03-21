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

class TestApi(make_docker_case('api', checks=["curl http://localhost:5000"])):
    """Test api docker instance"""
    pass

class TestCron(make_docker_case('cron', checks=[""])):
    """Test cron docker instance"""
    pass

class TestDashboard(make_docker_case('dashboard', checks=["curl http://localhost:3030"])):
    """Test dashboard docker instance"""
    pass

class TestWebserver(make_docker_case('webserver', checks=["curl http://localhost:7777"])):
    """Test webserver docker instance"""
    pass

class TestCadvisor(make_docker_case('cadvisor', checks=["curl http://localhost:8080"])):
    """Test cadvisor docker instance"""
    pass

if __name__ == '__main__':
    unittest.main()
