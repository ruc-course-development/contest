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

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


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
        """
        logging.debug('Constructing test case {}'.format(case_name))
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
        logging.info('Executing {} test case:'.format(self.case_name))

        test_args = [self.exe]
        test_args.extend(self.argv)
        stdin = '\n'.join(self.stdin)
        proc = subprocess.Popen(test_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = proc.communicate(input=stdin)
        
        errors = 0
        errors += self.check_streams('stdout', self.stdout, stdout)
        errors += self.check_streams('stderr', self.stderr, stderr)

        for ofstream in self.ofstreams:
            test_file = ofstream['test-file']
            file_name = ofstream['file-name']
            if test_file and file_name:
                with open(test_file, 'r') as tfile:
                    with open(file_name, 'r') as pfile:
                        errors += self.check_streams(file_name, tfile.read(), pfile.read())

        for extra_test in self.extra_tests:
            logging.info('    Executing: {}'.format(extra_test))
            extra_test = import_from_source(extra_test)
            if not extra_test.test():
                errors += 1
                logging.warn('    Failed!')
        
        return errors
                
    @staticmethod
    def check_streams(stream, expected, received):
        """
        Compares two output streams, line by line

        :param stream: name of stream being tested
        :param expected: expected content of stream
        :param received: stream output from the test
        :return: 0 for no errror, 1 for error
        """
        logging.info('    Executing {} stream test'.format(stream))
        for e, r in zip(re.split('\n+', expected), re.split('\n+', received)): 
            if e != r:
                logging.warn('    Failure:\n        Expected "{}"\n        Received "{}"'.format(e, r))
                return 1
        return 0


def test():
    """
    Run the specified test configuration
    """
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument('configuration', help='path to a YAML test configuration file')
    inputs = parser.parse_args()

    test_matrix = yaml.load(open(inputs.configuration, 'r'))
    executable = test_matrix['executable']
    test_cases = []
    for test_case in test_matrix['test-cases']:
        test = test_matrix['test-cases'][test_case]
        test_cases.append(TestCase(test_case,
                                executable if not test['executable'] else test['executable'],
                                test['argv'],
                                test['stdin'],
                                test['stdout'],
                                test['stderr'],
                                test['ofstreams'],
                                test['extra-tests']))

    errors = 0
    for test in test_cases:
        errors += test.execute()
        
    logging.info('{} errors found!'.format(errors if errors else 'No'))

if __name__ == '__main__':
    test()