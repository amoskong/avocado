#!/usr/bin/env python

import unittest
import os

from flexmock import flexmock, flexmock_teardown

from avocado.core import data_dir
from avocado.core import remote
from avocado.core import remoter
from avocado.utils import archive


cwd = os.getcwd()

JSON_RESULTS = ('Something other than json\n'
                '{"tests": [{"test": "sleeptest.1", "url": "sleeptest", '
                '"fail_reason": "None", '
                '"status": "PASS", "time": 1.23, "start": 0, "end": 1.23}],'
                '"debuglog": "/home/user/avocado/logs/run-2014-05-26-15.45.'
                '37/debug.log", "errors": 0, "skip": 0, "time": 1.4, '
                '"logdir": "/local/path/test-results/sleeptest", '
                '"logdir": "/local/path/test-results/sleeptest", '
                '"start": 0, "end": 1.4, "pass": 1, "failures": 0, "total": '
                '1}\nAdditional stuff other than json')


class RemoteTestRunnerTest(unittest.TestCase):

    """ Tests RemoteTestRunner """

    def setUp(self):
        flexmock(remote.RemoteTestRunner).should_receive('__init__')
        self.remote = remote.RemoteTestRunner(None, None)
        self.remote.job = flexmock(logdir='.')

        test_results = flexmock(stdout=JSON_RESULTS, exit_status=0)
        stream = flexmock(job_unique_id='sleeptest.1',
                          debuglog='/local/path/dirname')
        Remote = flexmock()
        args_version = 'avocado -v'
        version_result = flexmock(stdout='Avocado 1.2.3', exit_status=0)
        args_env = 'env'
        env_result = flexmock(stdout='''XDG_SESSION_ID=20
HOSTNAME=rhel7.0
SELINUX_ROLE_REQUESTED=
SHELL=/bin/bash
TERM=vt100
HISTSIZE=1000
SSH_CLIENT=192.168.124.1 52948 22
SELINUX_USE_CURRENT_RANGE=
SSH_TTY=/dev/pts/0
USER=root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/bin
MAIL=/var/spool/mail/root
PWD=/root
LANG=en_US.UTF-8
SELINUX_LEVEL_REQUESTED=
HISTCONTROL=ignoredups
HOME=/root
SHLVL=2
LOGNAME=root
SSH_CONNECTION=192.168.124.1 52948 192.168.124.65 22
LESSOPEN=||/usr/bin/lesspipe.sh %s
XDG_RUNTIME_DIR=/run/user/0
_=/usr/bin/env''', exit_status=0)
        (Remote.should_receive('run')
         .with_args(args_env, ignore_status=True, timeout=60)
         .once().and_return(env_result))

        (Remote.should_receive('run')
         .with_args(args_version, ignore_status=True, timeout=60)
         .once().and_return(version_result))

        args = 'cd ~/avocado/tests; avocado list sleeptest --paginator=off'
        urls_result = flexmock(exit_status=0)
        (Remote.should_receive('run')
         .with_args(args, timeout=60, ignore_status=True)
         .once().and_return(urls_result))

        args = ("cd ~/avocado/tests; avocado run --force-job-id sleeptest.1 "
                "--json - --archive sleeptest")
        (Remote.should_receive('run')
         .with_args(args, timeout=61, ignore_status=True)
         .once().and_return(test_results))
        Results = flexmock(remote=Remote, urls=['sleeptest'],
                           stream=stream, timeout=None,
                           args=flexmock(show_job_log=False))
        Results.should_receive('setup').once().ordered()
        Results.should_receive('copy_tests').once().ordered()
        Results.should_receive('start_tests').once().ordered()
        args = {'status': u'PASS', 'whiteboard': '', 'time_start': 0,
                'name': u'sleeptest.1', 'class_name': 'RemoteTest',
                'traceback': 'Not supported yet',
                'text_output': 'Not supported yet', 'time_end': 1.23,
                'tagged_name': u'sleeptest.1', 'time_elapsed': 1.23,
                'fail_class': 'Not supported yet', 'job_unique_id': '',
                'fail_reason': 'None',
                'logdir': '/local/path/test-results/sleeptest',
                'logfile': '/local/path/test-results/sleeptest/debug.log'}
        Results.should_receive('start_test').once().with_args(args).ordered()
        Results.should_receive('check_test').once().with_args(args).ordered()
        (Remote.should_receive('receive_files')
         .with_args('/local/path', '/home/user/avocado/logs/run-2014-05-26-'
                    '15.45.37.zip')).once().ordered()
        (flexmock(archive).should_receive('uncompress')
         .with_args('/local/path/run-2014-05-26-15.45.37.zip', '/local/path')
         .once().ordered())
        (flexmock(os).should_receive('remove')
         .with_args('/local/path/run-2014-05-26-15.45.37.zip').once()
         .ordered())
        Results.should_receive('end_tests').once().ordered()
        Results.should_receive('tear_down').once().ordered()
        self.remote.result = Results

    def tearDown(self):
        flexmock_teardown()

    def test_run_suite(self):
        """ Test RemoteTestRunner.run_suite() """
        self.remote.run_suite(None, None, 61)
        flexmock_teardown()  # Checks the expectations


class RemoteTestResultTest(unittest.TestCase):

    """ Tests the RemoteTestResult """

    def setUp(self):
        Remote = flexmock()
        Stream = flexmock()
        (flexmock(os).should_receive('getcwd')
         .and_return('/current/directory').ordered())
        Stream.should_receive('notify').once().ordered()
        remote_remote = flexmock(remoter)
        (remote_remote.should_receive('Remote')
         .with_args('hostname', 'username', 'password', 22)
         .once().ordered()
         .and_return(Remote))
        Args = flexmock(test_result_total=1,
                        url=['/tests/sleeptest', '/tests/other/test',
                             'passtest'],
                        remote_username='username',
                        remote_hostname='hostname',
                        remote_port=22,
                        remote_password='password',
                        remote_no_copy=False)
        self.remote = remote.RemoteTestResult(Stream, Args)

    def tearDown(self):
        flexmock_teardown()

    def test_setup(self):
        """ Tests RemoteTestResult.test_setup() """
        self.remote.setup()
        flexmock_teardown()

if __name__ == '__main__':
    unittest.main()
