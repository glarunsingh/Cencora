# Set up logging to write to a file
import logging

def create_log(name: str, level):
    logging.basicConfig(level=level, filename= name+".log", filemode='a',
                        datefmt="%Y-%m-%d %H:%M:%S",
                        format="%(asctime)s  %(filename)s  Line: %(lineno)d  %(levelname)s  Function_Name: %("
                        "funcName)s:  %(message)s")
    logger = logging.getLogger(name)

    package_to_silence = ['azure', 'langchain','httpx']

    # Stopping root logger in the log file
    for package_name in package_to_silence:
        root_logger = logging.getLogger(package_name)
        root_logger.setLevel(logging.CRITICAL)
        root_logger.propagate = False

    return logger