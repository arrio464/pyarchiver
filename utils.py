import functools
import logging
import sys

from colorlog import ColoredFormatter


class TerminalColors:
    NONE = "\033[0m"
    BOLD = "\033[1m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


def setup_logging(level: int = logging.DEBUG, filename: str = None):
    # Get the root logger
    logger = logging.getLogger()

    # Remove all existing handlers
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    # Prevent log propagation
    logger.propagate = False

    # Set the logging level
    logger.setLevel(level)

    # Create a custom colored formatter
    formatter = ColoredFormatter(
        "%(log_color)s[%(levelname).1s] %(filename)s:%(lineno)d: %(message)s%(reset)s",
        datefmt=None,
        log_colors={
            "DEBUG": "thin_white",
            "INFO": "cyan",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
            "SUCCESS": "green",
        },
    )

    # Add custom SUCCESS level
    logging.addLevelName(100, "SUCCESS")

    # Add success method to logger
    logger.success = functools.partial(logger.log, 100)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if filename is provided)
    if filename:
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
