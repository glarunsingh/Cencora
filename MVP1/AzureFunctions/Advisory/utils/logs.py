"""
Setting up logger
"""
import logging

def create_log(name: str, level):
    """
    Creates a logger with the specified name and logging level.

    Args:
        name (str): The name of the logger.
        level (int): The logging level.

    Returns:
        logging.Logger: The created logger.
    """
    logging.basicConfig(level=level, datefmt="%Y-%m-%d %H:%M:%S",
                        format="%(asctime)s  %(filename)s  Line: %(lineno)d  %(levelname)s  Function_Name: %("
                               "funcName)s  %(message)s")
    logger = logging.getLogger(name)

    package_to_silence = ['azure', 'langchain', 'httpx']

    # Stopping root logger in the log file
    for package_name in package_to_silence:
        root_logger = logging.getLogger(package_name)
        root_logger.setLevel(logging.CRITICAL)
        root_logger.propagate = False

    return logger