import logging
import sys


def setup_logger(name):
    """
    Configures a consistent logger for the application.
    Format: Timestamp - Module - Level - Function - Message
    """
    logger = logging.getLogger(name)

    # Prevent adding multiple handlers if function is called repeatedly
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Output to console (stdout)
        handler = logging.StreamHandler(sys.stdout)

        # The specific format requested: Metadata + Message
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [Func: %(funcName)s] - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
