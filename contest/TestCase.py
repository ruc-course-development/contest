import os
import pathlib
import re
from subprocess import Popen, PIPE, TimeoutExpired
from contest.utilities import chdir, which
from contest.utilities.importer import import_from_source
from contest.utilities.logger import logger, logger_format_fields



class TestCase():
    def __init__(self, case_name, exe, return_code, argv, stdin, stdout, stderr, ofstreams, extra_tests, timeout, test_home):
        """Initialize test case inputs

        Arguments:
            case_name (str): name of the test
            exe (str): executable to test
            return_code (int): return code of the execution
            argv (list): list of command line arguments
            stdin (list): list of inputs that are passed to stdin
            stdout (str): expected output to stdout
            stderr (str): expected output to stderr
            ofstreams (list): list of pairs of file names and content
            extra_tests (list): list of additional modules to load for testing
            test_home (str): directory to run the test out of
        """
        logger_format_fields['test_case'] = case_name
        logger.debug('Constructing test case {}'.format(case_name), extra=logger_format_fields)
        self.case_name = case_name
        self.exe = exe
        self.return_code = return_code
        self.argv = [a for a in argv]
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.ofstreams = ofstreams
        self.extra_tests = extra_tests
        self.timeout = timeout
        self.test_home = test_home
        os.makedirs(self.test_home, exist_ok=True)

        self.test_args = self._setup_test_process()

    def _setup_test_process(self):
        """Properly sets the relative paths for the executable and contructs the 
        argument list for the executable.

        Returns:
            list of the executable and arguments to be passed to Popen
        """
        splexe = self.exe.split()

        if pathlib.Path(os.path.join(self.test_home, '..', '..', splexe[0])).exists():
            splexe[0] = os.path.abspath(os.path.join(self.test_home, '..', '..', splexe[0]))
        elif which.on_path(splexe[0]) and len(splexe) > 1:
            if pathlib.Path(os.path.join(self.test_home, '..', '..', splexe[1])).exists():
                splexe[1] = os.path.abspath(os.path.join(self.test_home, '..', '..', splexe[1]))

        splexe.extend(self.argv)

        return splexe

    def execute(self):
        """Execute the test

        Returns:
            Number of errors encountered
        """
        logger_format_fields['test_case'] = self.case_name
        logger.critical('Starting test', extra=logger_format_fields)
        logger.debug('Test Home: {}'.format(self.test_home), extra=logger_format_fields)
        logger.debug('Running: {}'.format(self.test_args), extra=logger_format_fields)
        with chdir.ChangeDirectory(self.test_home):
            errors = 0
            try:
                proc = Popen(self.test_args, cwd=os.getcwd(), stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                stdout, stderr = proc.communicate(input=self.stdin, timeout=self.timeout)
            except TimeoutExpired as e:
                logger.critical('Your program took too long to run! Perhaps you have an infinite loop?', extra=logger_format_fields)
                proc.kill()
                stdout, stderr = proc.communicate()
                errors += 1
        
            errors += self.check_streams('stdout', self.stdout, stdout)
            errors += self.check_streams('stderr', self.stderr, stderr)

            if self.return_code and int(self.return_code) != proc.returncode:
                logger.critical('FAILURE:\n         Expected return code {}, received {}'.format(self.return_code, proc.returncode), extra=logger_format_fields)
                errors += 1

            for ofstream in self.ofstreams:
                test_file = ofstream['test-file']
                base_file = os.path.join('..', '..', ofstream['base-file'])
                if test_file and base_file:
                    with open(test_file, 'r') as tfile, open(base_file, 'r') as pfile:
                        errors += self.check_streams(base_file, tfile.read(), pfile.read())

            for extra_test in self.extra_tests:
                logger.debug('Running extra test: {}'.format(extra_test), extra=logger_format_fields)
                extra_test = import_from_source(extra_test)
                if not extra_test.test():
                    errors += 1
                    logger.critical('Failed!', extra=logger_format_fields)

            if not errors:
                logger.critical('OK!', extra=logger_format_fields)

        return int(errors > 0)

    @staticmethod
    def check_streams(stream, expected, received):
        """Compares two output streams, line by line

        Arguments:
            stream (str): name of stream being tested
            expected (str): expected content of stream
            received (str): stream output from the test

        Returns:
            0 for no errror, 1 for error
        """
        logger.debug('Comparing {} streams line by line'.format(stream), extra=logger_format_fields)
        for line_number, (e, r) in enumerate(zip(re.split('\n+', expected), re.split('\n+', received))):
            logger.debug('{} line {}:\n"{}"\n"{}"\n'.format(stream, line_number, e, r), extra=logger_format_fields)
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
                logger.critical('FAILURE:\n        Expected "{}"\n        Received "{}"\n                  {}'.format(e, r, error_location), extra=logger_format_fields)

                return 1
        return 0