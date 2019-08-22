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

    global logger
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(test_case)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)  # pylint: disable=E1101
    logger = logging.LoggerAdapter(logger, logger_format_fields)
