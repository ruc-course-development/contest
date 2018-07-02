#!/usr/bin/python3

import argparse
import importlib.util
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import yaml
from collections import OrderedDict


sys.dont_write_bytecode=True

__version__ = '0.1.0'
logger = logging.getLogger(__name__)
logger_format_fields = {
    'test_case': __file__
}

# https://stackoverflow.com/a/16782282
def represent_ordereddict(dumper, data):
    value = []
    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)
        value.append((node_key, node_value))
    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)

yaml.add_representer(OrderedDict, represent_ordereddict)

# https://stackoverflow.com/a/15423007
def should_use_block(value):
    for c in u"\u000a\u000d\u001c\u001d\u001e\u0085\u2028\u2029":
        if c in value:
            return True
    return False

def my_represent_scalar(self, tag, value, style=None):
    if style is None:
        if should_use_block(value):
             style='|'
        else:
            style = self.default_style
    node = yaml.representer.ScalarNode(tag, value, style=style)
    if self.alias_key is not None:
        self.represented_objects[self.alias_key] = node
    return node

yaml.representer.BaseRepresenter.represent_scalar = my_represent_scalar


# https://stackoverflow.com/a/21912744
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def record_test(command, test_name):
    """
    Record the input and output of the given command, placing it within a a
    test recipe

    :param command: list of strings forming a complete command to run
    :param test_name: name to save the test results under
    :return: 0 for success, otherwise return an error message
    """
    class RecorderPipe(threading.Thread):
        """
        Custom thread with a pipe for intercepting stdin ina  subprocess
        """
        def __init__(self):
            """
            Initialize the thread
            """
            threading.Thread.__init__(self)
            self.daemon = True

            self.lines = []
            self.process = None

            self.rd, self.wd = os.pipe()
            self.rpipe = os.fdopen(self.rd)
            self.wpipe = os.fdopen(self.wd, 'w')

            self.start()

        def fileno(self):
            """
            Returns the file descriptor of the read-end of the pipe

            :return: file descriptor
            """
            return self.rd

        def run(self):
            """
            Method for the running thread. Will yield until the external
            subprocess is hooked in and will continuw while the write-end of the
            pipe is open and the subprocess is still running.
            """
            while self.process is None:
                pass

            # TODO: potential race condition here? investigate later.
            while self.wpipe is not None and self.process.poll() is None:
                s = input()
                self.wpipe.write(s + '\n')
                self.wpipe.flush()
                self.lines.append(s)
                # TODO: is this necessary? investigate later.
                self.check()

        def check(self):
            """
            Check if the subprocess is opened, and if it is not, cleanup
            """
            if self.process.poll() is not None:
                self.close()

        def close(self):
            """
            Close both ends of the pipe and set the write-end to None
            """
            self.rpipe.close()
            self.wpipe.close()
            self.wpipe = None

    def get_files(root):
        files = []
        for el in os.listdir(root):
            full_path = os.path.join(root, el)
            if os.path.isfile(full_path):
                files.append(full_path)
            else:
                files.extend(get_files(full_path))
        return files

    logger.debug('Starting test with command "{}"'.format(command))
    recorder_pipe = RecorderPipe()

    files = set(get_files('.'))

    proc = subprocess.Popen(command, stdin=recorder_pipe, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    recorder_pipe.process = proc
    stdout, stderr = proc.communicate()
    logger.debug('Test complete... writing to recipe...')

    new_files = set(get_files('.')) - files

    if os.path.exists('contest_recipe.yaml'):
        with open('contest_recipe.yaml', 'r') as recipe:
            test_recipe = ordered_load(recipe, yaml.SafeLoader)
        if test_name in test_recipe['test-cases']:
            return '{} is already a test case! Choose a new name!'.format(test_name)
        test_recipe['test-cases'][test_name] = OrderedDict()
        test_case = test_recipe['test-cases'][test_name]
        if command[0] != test_recipe['executable']:
            test_case['executable'] = command[0]
    else:
        test_recipe = OrderedDict()
        test_recipe['executable'] = command[0]
        test_recipe['test-cases'] = OrderedDict()
        test_recipe['test-cases'][test_name] = OrderedDict()
        test_case = test_recipe['test-cases'][test_name]

    test_case['return-code'] = proc.returncode

    argv = command[1:]
    if argv:
        test_case['argv'] = command[1:]
    if recorder_pipe.lines:
        test_case['stdin'] = recorder_pipe.lines
    if stdout:
        test_case['stdout'] = stdout
    if stderr:
        test_case['stderr'] = stderr

    if new_files:
        test_case['ofstreams'] = []
        for new_file in new_files:
            dir_name, file_name = os.path.split(new_file)
            base_file = os.path.join(dir_name, 'contest_' + file_name)
            shutil.move(new_file, base_file)
            test_case['ofstreams'].append(OrderedDict())
            test_case['ofstreams'][-1]['base-file'] = base_file
            test_case['ofstreams'][-1]['test-file'] = new_file

    recipe = open('contest_recipe.yaml', 'w')
    yaml.dump(test_recipe, recipe)
    return 0


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


class chdir:
    """
    Temporary directory change for context statements.
    """
    def __init__(self, path):
        self.old_path = os.getcwd()
        self.new_path = path = path
    def __enter__(self):
        os.chdir(self.new_path)
    def __exit__(self, type, value, traceback):
        os.chdir(self.old_path)


def import_from_source(path, add_to_modules=False):
    """
    Imports a Python source file using its path on the system.

    :param path: path to the source file. may be relative.
    :param add_to_modules: indicate whether to not to add to sys.modules
    """
    module_name = os.path.splitext(os.path.basename(path))[1]
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if add_to_modules:
        sys.modules[module_name] = module
    return module


class TestCase():
    def __init__(self, case_name, exe, return_code, argv, stdin, stdout, stderr, ofstreams, extra_tests, test_home):
        """
        Initialize test case inputs

        :param case_name: name of the test
        :param exe: executable to test
        :param return_code: return code of the execution
        :param argv: list of command line arguments
        :param stdin: list of inputs that are passed to stdin
        :param stdout: expected output to stdout
        :param stderr: expected output to stderr
        :param ofstreams: list of pairs of file names and content
        :param extra_tests: list of additional modules to load for testing
        :param test_home: directory to run the test out of
        """
        logger.debug('Constructing test case {}'.format(case_name))
        self.case_name = case_name
        self.exe = exe
        self.return_code = return_code
        self.argv = [a for a in argv]
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.ofstreams = ofstreams
        self.extra_tests = extra_tests
        self.test_home = test_home
        os.makedirs(self.test_home, exist_ok=True)

        self.test_args = self._setup_test_process()


    def _setup_test_process(self):
        """
        Properly sets the relative paths for the executable and contructs the 
        argument list for the executable.

        :return: list of the executable and arguments to be passed to Popen
        """
        test_args = []
        splexe = self.exe.split()
        if len(splexe) == 1:
            test_args.append(os.path.abspath(os.path.join(self.test_home, '..', '..', self.exe)))
        elif len(splexe) == 2:
            splexe[1] = os.path.abspath(os.path.join(self.test_home, '..', '..', splexe[1]))
            test_args.extend(splexe)
        test_args.extend(self.argv)
        return test_args


    def execute(self):
        """
        Execute the test

        :return: number of errors encountered
        """
        logger_format_fields['test_case'] = 'test={}'.format(self.case_name)
        logger.critical('Starting test')

        logger.debug('Running: {}'.format(self.test_args))
        with chdir(self.test_home):
            proc = subprocess.Popen(self.test_args, cwd=os.getcwd(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = proc.communicate(input=self.stdin)
        
            errors = 0
            errors += self.check_streams('stdout', self.stdout, stdout)
            errors += self.check_streams('stderr', self.stderr, stderr)

            if self.return_code and int(self.return_code) != proc.returncode:
                logger.critical('FAILURE:\n         Expected return code {}, received {}'.format(self.return_code, proc.returncode))
                errors += 1

            for ofstream in self.ofstreams:
                test_file = ofstream['test-file']
                base_file = os.path.join('..', '..', ofstream['base-file'])
                if test_file and base_file:
                    with open(test_file, 'r') as tfile, open(base_file, 'r') as pfile:
                        errors += self.check_streams(base_file, tfile.read(), pfile.read())

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
    """Run the specified test configuration"""
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument('configuration', help='path to a YAML test configuration file')
    parser.add_argument('--filters', default=[], nargs='+', help='regex pattern for tests to match')    
    parser.add_argument('--exclude-filters', default=[], nargs='+', help='regex pattern for tests to match')    
    parser.add_argument('--generate', nargs='+', help='executable and arguments to generate a test for')    
    parser.add_argument('--new-test-name', help='name for the test being generated; name must be unused already')    
    parser.add_argument('--verbose', action='store_true', default=False, help='verbose output')
    parser.add_argument('--version', action='version', version='contest.py v{}'.format(__version__))
    inputs = parser.parse_args()

    setup_logger(inputs.verbose)

    if inputs.generate:
        if not inputs.new_test_name:
            return 'You must specify --new-test-name <name> when generating a new test!'
        
        return record_test(inputs.generate, inputs.new_test_name)
    else:
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
                                executable if not test.get('executable', '') else test['executable'],
                                test.get('return-code', None),
                                test.get('argv', []),
                                test.get('stdin', ''),
                                test.get('stdout', ''),
                                test.get('stderr', ''),
                                test.get('ofstreams', {}),
                                test.get('extra-tests', []),
                                os.path.join(os.path.dirname(inputs.configuration), 'test_output', test_case)))

        errors = 0
        for test in tests:
            errors += test.execute()
            logger_format_fields['test_case'] = __file__

        logger.critical('{}/{} tests passed!'.format(number_of_tests_to_run-errors, number_of_tests_to_run))
        return errors


if __name__ == '__main__':
    sys.exit(test())