import pathlib
import re
from subprocess import run, PIPE, TimeoutExpired
from contest.utilities import chdir
from contest.utilities.importer import import_from_source
from contest.utilities.logger import logger, logger_format_fields


class TestCase():
    def __init__(self, case_name, exe, return_code, argv, stdin, stdout, stderr, ofstreams, env, extra_tests, timeout, test_home):
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
            env (dict): dictionary of environment variables to set in the execution space
            extra_tests (list): list of additional modules to load for testing
            test_home (str): directory to run the test out of
        """
        logger_format_fields['test_case'] = case_name
        logger.debug(f'Constructing test case {case_name}', extra=logger_format_fields)
        self.case_name = case_name
        self.exe = exe
        self.return_code = return_code
        self.argv = [a for a in argv]
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.ofstreams = ofstreams
        self.env = env
        self.extra_tests = extra_tests
        self.timeout = timeout
        self.test_home = test_home
        pathlib.Path(self.test_home).mkdir(parents=True, exist_ok=True)

        self.test_args = self._setup_test_process()

    def _setup_test_process(self):
        """Properly sets the relative paths for the executable and contructs the
        argument list for the executable.

        Returns:
            list of the executable and arguments to be passed to subprocess.run
        """
        splexe = self.exe.split()
        splexe.extend(self.argv)
        for idx, sp in enumerate(splexe):
            sp = pathlib.Path(self.test_home, '..', '..', sp)
            if sp.exists():
                sp = sp.resolve()
                splexe[idx] = str(sp)
        return splexe

    def execute(self):
        """Execute the test

        Returns:
            Number of errors encountered
        """
        logger_format_fields['test_case'] = self.case_name
        logger.critical('Starting test', extra=logger_format_fields)
        logger.debug(f'Test Home: {self.test_home}', extra=logger_format_fields)
        logger.debug(f'Running: {self.test_args}', extra=logger_format_fields)
        with chdir.ChangeDirectory(self.test_home):
            errors = 0
            try:
                proc = run(self.test_args, input=self.stdin, stdout=PIPE, stderr=PIPE, cwd=pathlib.Path.cwd(), timeout=self.timeout, universal_newlines=True, env=self.env)
            except TimeoutExpired:
                logger.critical('Your program took too long to run! Perhaps you have an infinite loop?', extra=logger_format_fields)
                errors += 1

            errors += self.check_streams('stdout', self.stdout, proc.stdout)
            errors += self.check_streams('stderr', self.stderr, proc.stderr)

            if self.return_code and int(self.return_code) != proc.returncode:
                logger.critical(f'FAILURE:\n         Expected return code {self.return_code}, received {proc.returncode}', extra=logger_format_fields)
                errors += 1

            for ofstream in self.ofstreams:
                test_file = ofstream['test-file']
                base_file = pathlib.Path('..', '..', ofstream['base-file'])
                if test_file and base_file:
                    with open(test_file, 'r') as tfile, open(base_file, 'r') as pfile:
                        errors += self.check_streams(base_file, tfile.read(), pfile.read())

            for extra_test in self.extra_tests:
                logger.debug(f'Running extra test: {extra_test}', extra=logger_format_fields)
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
        logger.debug(f'Comparing {stream} streams line by line', extra=logger_format_fields)
        for line_number, (e, r) in enumerate(zip(re.split('\n+', expected), re.split('\n+', received))):
            logger.debug(f'{stream} line {line_number}:\n"{e}"\n"{r}"\n', extra=logger_format_fields)
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
                e = f'        Expected "{e}"'
                r = f'        Received "{r}"'
                error_location = (' '*18) + (' '*i) + '^ ERROR'
                logger.critical(f'FAILURE:\n{e}\n{r}\n{error_location}', extra=logger_format_fields)
                return 1
        return 0
