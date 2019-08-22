import logging


logger = logging.getLogger(__name__)
logger_format_fields = {
    'test_case': __file__
}


def setup_logger(is_verbose):
    """Configure the logger for contest.py

    Arguments:
        level (bool): logging level
    """
    verbosity_mapping = {
        False: logging.CRITICAL,
        True: logging.DEBUG
    }

    level = verbosity_mapping[is_verbose]

    class Formatter(logging.Formatter):
        def format(self, record):
            """Format the message conditionally

            Arguments:
                record (str): incoming message information

            Returns:
                updated message information
            """
            if record.levelno == logging.DEBUG:
                s = '%(message)s'
            else:
                s = '%(test_case)s - %(message)s'
            self._style._fmt = s
            s = logging.Formatter.format(self, record)
            return s

    global logger
    global logger_format_fields
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = Formatter()
    ch.setFormatter(formatter)
    logger.addHandler(ch)  # pylint: disable=E1101
    logger = logging.LoggerAdapter(logger, logger_format_fields)