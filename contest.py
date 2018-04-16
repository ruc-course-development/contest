#!/usr/bin/python3

import argparse
import importlib.util
import logging
import os
import re
import subprocess
import sys
import yaml
sys.dont_write_bytecode=True

__version__ = '0.1.0'

logger = logging.getLogger(__name__)
logger_format_fields = {
    'test_case': __file__
}


def setup_logger(is_verbose):
    """
    Configure the logger for contest.py

    :param level: logging level
    :return:
    """
    verbosity_mapping = {
        False:logging.CRITICAL,
        True:logging.DEBUG
    }

    level = verbosity_mapping[is_verbose]

    class Formatter(logging.Formatter):
        def format(self, record):
            """
            Format the message conditionally

            :param record: incoming message information
            :return: updated message information
            """
            if record.levelno == logging.DEBUG:
                s = '%(message)s'
            else:
                s = '%(test_case)s - %(message)s'
            self._style._fmt = s
            s = logging.Formatter.format(self, record)
            return s

    global logger
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = Formatter()
    ch.setFormatter(formatter)
    logger.addHandler(ch) # pylint: disable=E1101

    logger = logging.LoggerAdapter(logger, logger_format_fields)


def import_from_source(path, add_to_modules=False):
    """
    Imports a Python source file using its path on the system.

    :param path: path to the source file. may be relative.
    :param add_to_modules: indicate whether to not to add to sys.modules
    :return: 
    """
    module_name = os.path.splitext(os.path.basename(path))[1]
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if add_to_modules:
        sys.modules[module_name] = module
    return module


class TestCase():
    def __init__(self, case_name, exe, argv, stdin, stdout, stderr, ofstreams, extra_tests):
        """
        Initialize test case inputs

        :param case_name: name of the test
        :param exe: executable to test
        :param argv: list of command line arguments
        :param stdin: list of inputs that are passed to stdin
        :param stdout: expected output to stdout
        :param stderr: expected output to stderr
        :param ofstreams: list of pairs of file names and content
        :param extra_tests: list of additional modules to load for testing
        :return:
        """
        logger.debug('Constructing test case {}'.format(case_name))
        self.case_name = case_name
        self.exe = exe
        self.argv = [a for a in argv]
        self.stdin = [i for i in stdin]
        self.stdout = stdout
        self.stderr = stderr
        self.ofstreams = ofstreams
        self.extra_tests = extra_tests

    def execute(self):
        """
        Execute the test

        :return: number of errors encountered
        """
        logger_format_fields['test_case'] = 'test={}'.format(self.case_name)
        logger.critical('Starting test')

        test_args = [self.exe]
        test_args.extend(self.argv)

        cwd = os.path.dirname(self.exe)

        logger.debug('Running: {}'.format(test_args))
        proc = subprocess.Popen(test_args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        stdin = '\n'.join(self.stdin)
        stdout, stderr = proc.communicate(input=stdin)
        
        errors = 0
        errors += self.check_streams('stdout', self.stdout, stdout)
        errors += self.check_streams('stderr', self.stderr, stderr)

        for ofstream in self.ofstreams:
            test_file = ofstream['test-file']
            file_name = ofstream['file-name']
            if test_file and file_name:
                test_file = os.path.join(cwd, test_file)
                file_name = os.path.join(cwd, file_name)
                with open(test_file, 'r') as tfile:
                    with open(file_name, 'r') as pfile:
                        errors += self.check_streams(file_name, tfile.read(), pfile.read())

        for extra_test in self.extra_tests:
            logger.debug('Running extra test: {}'.format(extra_test))
            extra_test = import_from_source(extra_test)
            if not extra_test.test():
                errors += 1
                logger.critical('Failed!')
        
        if not errors:
            logger.critical('OK!')

        return int(errors>0)
                
    @staticmethod
    def check_streams(stream, expected, received):
        """
        Compares two output streams, line by line

        :param stream: name of stream being tested
        :param expected: expected content of stream
        :param received: stream output from the test
        :return: 0 for no errror, 1 for error
        """
        logger.debug('Comparing {} streams line by line'.format(stream))
        for line_number, (e, r) in enumerate(zip(re.split('\n+', expected), re.split('\n+', received))):
            logger.debug('{} line {}:\n"{}"\n"{}"\n'.format(stream, line_number, e, r))
            if e != r:
                i = 0
                while True:
                    s1 = e[i:i+5]
                    s2 = r[i:i+5]

                    if not s1 == s2:
                        for idx, (a, b) in enumerate(zip(s1, s2)):
                            if not a == b:
                                i = i + idx
                                break
                        else:
                            i = i + min(len(s1), len(s2))
                        break

                    i = i + 5
                error_location = (' '*i) + '^ ERROR'
                logger.critical('FAILURE:\n        Expected "{}"\n        Received "{}"\n                  {}'.format(e, r, error_location))

                return 1
        return 0


def filter_tests(case_name, includes, excludes):
    """
    Check if the input case is valid

    :param case_name: name of case
    :param includes: list of regex patterns to check against
    :param excludes: list of regex patterns to check against
    :return: True is valid, False otherwise
    """
    for re_filter in excludes:
        if re.search(re_filter, case_name):
            logger.debug('Excluding {}, matches pattern {}'.format(case_name, re_filter))
            return False

    if not includes:
        return True

    for re_filter in includes:
        if re.search(re_filter, case_name):
            logger.debug('Including {}, matches pattern {}'.format(case_name, re_filter))
            return True
    return False


def test():
    """
    Run the specified test configuration

    :return:
    """
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument('configuration', help='path to a YAML test configuration file')
    parser.add_argument('--filters', default=[], nargs='+', help='regex pattern for tests to match')    
    parser.add_argument('--exclude-filters', default=[], nargs='+', help='regex pattern for tests to match')    
    parser.add_argument('--verbose', action='store_true', default=False, help='verbose output')
    parser.add_argument('--version', action='version', version='contest.py v{}'.format(__version__))
    inputs = parser.parse_args()

    setup_logger(inputs.verbose)

    logger.critical('Loading {}'.format(inputs.configuration))
    test_matrix = yaml.load(open(inputs.configuration, 'r'))
    executable = test_matrix['executable']

    number_of_tests = len(test_matrix['test-cases'])
    logger.critical('Found {} tests'.format(number_of_tests))

    test_cases = [case for case in test_matrix['test-cases'] if filter_tests(case, inputs.filters, inputs.exclude_filters)]
    number_of_tests_to_run = len(test_cases)
    logger.critical('Running {} tests'.format(number_of_tests_to_run))

    tests = []
    for test_case in test_cases:
        test = test_matrix['test-cases'][test_case]
        tests.append(TestCase(test_case,
                                executable if not test['executable'] else test['executable'],
                                test['argv'],
                                test['stdin'],
                                test['stdout'],
                                test['stderr'],
                                test['ofstreams'],
                                test['extra-tests']))

    errors = 0
    for test in tests:
        errors += test.execute()
        logger_format_fields['test_case'] = __file__

    logger.critical('{}/{} tests passed!'.format(number_of_tests_to_run-errors, number_of_tests_to_run))

if __name__ == '__main__':
    test()