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
            logger.debug(f'Excluding {case_name}, matches pattern {re_filter}', extra=logger_format_fields)
            return False

    if not includes:
        return True

    for re_filter in includes:
        if re.search(re_filter, case_name):
            logger.debug(f'Including {case_name}, matches pattern {re_filter}', extra=logger_format_fields)
            return True
    return False


def test():
    """Run the specified test configuration"""
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument('configuration', help='path to a YAML test configuration file')
    parser.add_argument('--fail', action='store_true', default=False, help='end execution on first failure')
    parser.add_argument('--filters', default=[], nargs='+', help='regex pattern for tests to match')
    parser.add_argument('--exclude-filters', default=[], nargs='+', help='regex pattern for tests to match')
    parser.add_argument('--verbose', action='store_true', default=False, help='verbose output')
    parser.add_argument('--version', action='version', version=f'contest.py v{__version__.__version__}')
    inputs = parser.parse_args()

    setup_logger(inputs.verbose)
    logger_format_fields['test_case'] = 'contest'

    logger.critical(f'Loading {inputs.configuration}', extra=logger_format_fields)
    test_matrix = yaml.load(open(inputs.configuration, 'r'), Loader=DefaultLoader)
    logger.debug(f'{inputs.configuration} Loaded', extra=logger_format_fields)
    executable = test_matrix.get('executable', '')
    logger.debug(f'Root executable: {executable}', extra=logger_format_fields)

    number_of_tests = len(test_matrix['test-cases'])
    logger.critical(f'Found {number_of_tests} tests', extra=logger_format_fields)
    test_cases = [case for case in test_matrix['test-cases'] if filter_tests(case['name'], inputs.filters, inputs.exclude_filters)]
    number_of_tests_to_run = len(test_cases)
    logger.critical(f'Running {number_of_tests_to_run} tests', extra=logger_format_fields)

    tests = []
    for test_case in test_cases:
        tests.append(
            TestCase(
                test_case['name'],
                test_case.get('executable', executable),
                test_case.get('return-code', None),
                test_case.get('argv', []),
                test_case.get('stdin', ''),
                test_case.get('stdout', ''),
                test_case.get('stderr', ''),
                test_case.get('ofstreams', []),
                test_case.get('env', {}) if test_case.get('scrub-env', False) else {**os.environ, **test_case.get('env', {})},
                test_case.get('extra-tests', []),
                test_case.get('timeout', None),
                os.path.join(os.path.dirname(inputs.configuration), 'test_output', test_case['name']),
                test_case.get('resources', []),
                test_case.get('setup', []),
            )
        )

    errors = 0
    tests_run = 0
    for test in tests:
        errors += test.execute()
        tests_run += 1
        if inputs.fail and errors:
            logger_format_fields['test_case'] = 'contest'
            logger.critical('Breaking on first failue', extra=logger_format_fields)
            break

    logger_format_fields['test_case'] = 'contest'

    logger.critical(f'{tests_run-errors}/{tests_run} tests passed!', extra=logger_format_fields)
    return errors


if __name__ == '__main__':
    sys.exit(test())
