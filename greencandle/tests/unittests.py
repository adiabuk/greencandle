#pylint: disable=wrong-import-position,no-member,broad-except,too-many-instance-attributes,too-many-arguments,logging-not-lazy,no-else-break

"""
Helper classes and functions for creating and running unittests
"""

import unittest
import os
import subprocess
import time

from greencandle.lib import config
config.create_config()

from greencandle.lib.binance_common import get_data
from greencandle.lib.logger import get_logger
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.lib.run import perform_data
from greencandle.lib.graph import Graph

def get_tag():
    """
    Get release tag from environment
    """

    if not 'GIT_BRANCH' in os.environ:
        tag = 'latest'
    elif os.environ['GIT_BRANCH'] == 'master':
        tag = 'latest'
    else:
        tag = 'release-{}'.format(os.environ['GIT_BRANCH'])
    return tag

class OrderedTest(unittest.TestCase):
    """
    Custom unittest class which allows test methods to be run sequentially
    """
    def assert_raises_with_message(self, msg, func, *args, **kwargs):
        """ensure exception is raised with a specific message"""
        try:
            func(*args, **kwargs)
            self.assertFail()
        except Exception as inst:
            self.assertEqual(inst.message, msg)

    def _steps(self):
        """
        Get lists of steps that are to be run
        methods should be called "step_n" where n denotes the sequence of execution
        """
        for name in dir(self): # dir() result is implicitly sorted
            if name.startswith("step"):
                yield name, getattr(self, name)

    def test_steps(self):
        """
        Run test steps in sequence
        """
        for name, step in self._steps():
            try:
                print("step", name)
                step()
            except Exception as exc:
                self.fail("{} failed ({}: {})".format(step, type(exc), exc))

def make_docker_case(container, checks=None):
    """
    return docker unittest customized with argument config
    """
    class DockerRun(OrderedTest):
        """
        Test given docker instance with given check commands
        """
        def __init__(self, *args, **kwargs):
            super(DockerRun, self).__init__(*args, **kwargs)
            self.compose_file = 'install/docker-compose_unit.yml'
            self.build_id = os.environ['id']

        def run_subprocess(self, command):
            """
            Run given command using subprocess and return exit code
            """

            self.logger.info("Running command: %s" % command)
            process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, shell=True)
            while process.poll() is None:
                # Process hasn't exited yet, let's wait some
                time.sleep(0.5)

            out, err = process.communicate()
            conv = lambda i: i or b''
            return (process.returncode,
                    conv(out).decode('utf-8').strip(),
                    conv(err).decode('utf-8').strip())

        def setUp(self):
            self.logger = get_logger(__name__)

        def tearDown(self):
            self.logger.info("Cleanup up docker instances")
            command = ("TAG={} docker compose -f {} -p {} down"
                       .format(get_tag(), self.compose_file, self.build_id))
            self.run_subprocess(command)

        def step_1(self):
            """Start Instance"""

            self.logger.info("Starting instance %s", container)
            command = "TAG={} docker compose -f {} -p {}  up -d {} ".format(
                get_tag(), self.compose_file, self.build_id, container)
            return_code, out, err = self.run_subprocess(command)
            if err:
                self.logger.critical(err)
            elif out:
                self.logger.info(out)
            self.assertEqual(return_code, 0)

        def step_2(self):
            """Check instance is still running"""
            command = ('docker ps --format "{{.Names}}"  -f name=' + container
                       +'-{}'.format(self.build_id))

            for num in range(1, 11):
                # try 10 times before giving up
                print("running: {} attempt:{}".format(command, num))
                return_code, stdout, stderr = self.run_subprocess(command)
                if return_code == 0:
                    break
                else:
                    time.sleep(10)

            self.assertEqual(return_code, 0)
            self.assertIn(container, stdout)
            self.assertEqual(stderr, "")

        def step_3(self):
            """Run healthchecks"""
            if checks:
                for check in checks:
                    for num in range(1, 21):

                        command = "docker exec {} {}".format(container+'-'+self.build_id, check)
                        print("running: {} attempt:{}".format(command, num))
                        return_code, stdout, stderr = self.run_subprocess(command)

                        print("stdout: {}. stderr: {}".format(stdout, stderr))
                        if return_code == 0:
                            break
                        else:
                            time.sleep(10)

                    self.assertEqual(return_code, 0)

        def step_4(self):
            """check health status"""
            command = ('docker ps --format "{{.Status}}"  -f name=' + container +
                       "-{}".format(self.build_id))
            for num in range(1, 11):
                print("running: {} attempt:{}".format(command, num))
                stdout = self.run_subprocess(command)[1]
                print("stdout: {}".format(stdout))

                if "unhealthy" not in stdout and "starting" not in stdout:
                    break
                else:
                    time.sleep(10)

            self.assertIn("healthy", stdout)
            self.assertNotIn("unhealthy", stdout)
            self.assertNotIn("starting", stdout)

    return DockerRun

def run_subprocess(command):
    """
    Run given command using subprocess and return exit code
    """
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, shell=True)
    while process.poll() is None:
        # Process hasn't exited yet, let's wait some
        time.sleep(0.5)

    out, err = process.communicate()
    conv = lambda i: i or b''
    return (process.returncode,
            conv(out).decode('utf-8').strip(),
            conv(err).decode('utf-8').strip())

def make_test_case(config_env, pair, interval, startdate, days, xsum, xmax, xmin,
                   drawup, drawdown):
    """
    return run unittest customized with argument config
    """
    class UnitRun(OrderedTest):
        """
        Sequential unit tests which download data from binance, run process, and collect results
        Items checked:
                       * pickle file
                       * mysql/redis connection
                       * results
        """

        def setUp(self):
            """
            Define static instance variables and create redis/mysql objects as well as working test
            directory
            """

            self.pair = pair
            self.startdate = startdate
            self.sum = xsum
            self.max = xmax
            self.min = xmin
            self.drawup = drawup
            self.drawdown = drawdown

            os.system("configstore package process_templates {} /etc".format(config_env))
            config.create_config()  # reload config
            self.days = days
            self.outputdir = "/data/test_data"
            self.interval = interval
            self.logger = get_logger(__name__)
            self.logger.info("Setting up environment")
            self.redis = Redis(test_data=True)
            self.dbase = Mysql(test=True, interval=self.interval)
            if not os.path.exists(self.outputdir):
                os.mkdir(self.outputdir)

        def step_1(self):
            """
            Step 1 - get test data
            """

            self.logger.info("Getting test data")
            print(self.startdate, self.interval, self.pair, self.days, self.outputdir)
            get_data(self.startdate, [self.interval], [self.pair], self.days, self.outputdir,
                     extra=200)

            filename = self.outputdir + '/' + self.pair + '_' + self.interval + '.p'
            self.logger.info("Filename: %s", filename)
            assert os.path.exists(filename) == 1

        def step_2(self):
            """
            Step 2 - execute test run
            """
            self.logger.info("Executing serial test run")
            main_indicators = config.main.indicators.split()
            perform_data(self.pair, self.interval, self.outputdir, main_indicators)
            assert True

        def step_3(self):
            """
            Step 3 - collect and compare data
            """
            self.logger.info("Comparing mysql data")
            self.dbase = Mysql(test=True, interval=self.interval)
            db_sum = self.dbase.fetch_sql_data("select sum(perc) from profit", header=False)[0][0]
            db_min = self.dbase.fetch_sql_data("select min(perc) from profit", header=False)[0][0]
            db_max = self.dbase.fetch_sql_data("select max(perc) from profit", header=False)[0][0]
            self.logger.info("DB_SUM: %s", db_sum)
            self.logger.info("DB_MAX: %s", db_max)
            self.logger.info("DB_MIN: %s", db_min)

            self.assertGreaterEqual(float(db_sum), self.sum)
            self.assertGreaterEqual(float(db_max), self.max)
            self.assertGreaterEqual(float(db_min), self.min)

        def step_4(self):
            """
            Step 4 - Compare drawdown and draw up from db
            """
            up_sum = self.dbase.fetch_sql_data("select sum(drawup_perc) from profit",
                                               header=False)[0][0]
            down_sum = self.dbase.fetch_sql_data("select sum(drawdown_perc) from profit",
                                                 header=False)[0][0]
            self.assertGreaterEqual(float(up_sum), self.drawup)
            self.assertGreaterEqual(float(down_sum), self.drawdown)

        def step_5(self):
            """
            Step 5 - Create graphs
            """
            self.logger.info("Creating graph")
            graph = Graph(test=False, pair=self.pair, interval=self.interval, volume=False)
            graph.get_data()
            graph.create_graph(output_dir=self.outputdir)

        def tearDown(self):
            """Cleanup DB and files"""
            self.logger.info("Cleaning up and gathering artifact")
            os.popen("mysqldump -h mysql -u root -ppassword greencandle > /tmp/output.sql")
            self.redis.clear_all()
            self.dbase.delete_data()
            del self.redis
            del self.dbase

    return UnitRun
