# llm_evaluator/utils/logging.py

import logging

def setup_logger(name: str, level=logging.DEBUG):
    """
    Setup and return a configured logger.
    
    :param name: Logger name.
    :param level: Logging level.
    :return: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
