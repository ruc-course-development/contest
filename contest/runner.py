import argparse
import os
import re
import sys
import yaml
from contest import __version__
from contest.TestCase import TestCase
from contest.utilities import configure_yaml  # noqa: F401
from contest.utilities.logger import logger, logger_format_fields, setup_logger
# PyYAML 3.12 compatibility
try:
    from yaml import FullLoader as DefaultLoader
except ImportError:
    from yaml import Loader as DefaultLoader

sys.dont_write_bytecode = True


def filter_tests(case_name, includes, excludes):
    """Check if the input case is valid

    Arguments:
        case_name (str): name of case
        includes (list): list of regex patterns to check against
        excludes (list): list of regex patterns to check against

    Returns:
        True is valid, False otherwise
    """
    for re_filter in excludes:
        if re.search(re_filter, case_name):
            logger.debug('Excluding {}, matches pattern {}'.format(case_name, re_filter), extra=logger_format_fields)
            return False

    if not includes:
        return True

    for re_filter in includes:
        if re.search(re_filter, case_name):
            logger.debug('Including {}, matches pattern {}'.format(case_name, re_filter), extra=logger_format_fields)
            return True
    return False


def test():
    """Run the specified test configuration"""
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument('configuration', help='path to a YAML test configuration file')
    parser.add_argument('--filters', default=[], nargs='+', help='regex pattern for tests to match')
    parser.add_argument('--exclude-filters', default=[], nargs='+', help='regex pattern for tests to match')
    parser.add_argument('--verbose', action='store_true', default=False, help='verbose output')
    parser.add_argument('--version', action='version', version='contest.py v{}'.format(__version__.__version__))
    inputs = parser.parse_args()

    setup_logger(inputs.verbose)
    logger_format_fields['test_case'] = 'contest'

    logger.critical('Loading {}'.format(inputs.configuration), extra=logger_format_fields)
    test_matrix = yaml.load(open(inputs.configuration, 'r'), Loader=DefaultLoader)
    executable = test_matrix['executable']

    number_of_tests = len(test_matrix['test-cases'])
    logger.critical('Found {} tests'.format(number_of_tests), extra=logger_format_fields)

    test_cases = [case for case in test_matrix['test-cases'] if filter_tests(case, inputs.filters, inputs.exclude_filters)]
    number_of_tests_to_run = len(test_cases)
    logger.critical('Running {} tests'.format(number_of_tests_to_run), extra=logger_format_fields)

    tests = []
    for test_case in test_cases:
        test = test_matrix['test-cases'][test_case]
        tests.append(TestCase(test_case,
                              test.get('executable', executable),
                              test.get('return-code', None),
                              test.get('argv', []),
                              test.get('stdin', ''),
                              test.get('stdout', ''),
                              test.get('stderr', ''),
                              test.get('ofstreams', {}),
                              {**os.environ, **test.get('env', {})},
                              test.get('extra-tests', []),
                              test.get('timeout', None),
                              os.path.join(os.path.dirname(inputs.configuration), 'test_output', test_case)))

    errors = 0
    for test in tests:
        errors += test.execute()

    logger_format_fields['test_case'] = 'contest'

    logger.critical('{}/{} tests passed!'.format(number_of_tests_to_run-errors, number_of_tests_to_run), extra=logger_format_fields)
    return errors


if __name__ == '__main__':
    sys.exit(test())
