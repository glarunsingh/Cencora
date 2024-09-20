import os
import logging
from config.key_vault import key_vault
secret_value = key_vault()

from opencensus.ext.azure.log_exporter import AzureLogHandler
APPLICATION_INSIGHTS_STRING_WEBAPP = secret_value.get_secret('APPLICATION-INSIGHTS-STRING-WEBAPP')

def create_log(level):

    logger = logging.getLogger()
    handler = AzureLogHandler(connection_string = APPLICATION_INSIGHTS_STRING_WEBAPP)
    logging.basicConfig(level=level,datefmt="%Y-%m-%d %H:%M:%S",
                        format="%(asctime)s  %(filename)s  Line: %(lineno)d  %(levelname)s  Function_Name: %("
                        "funcName)s  %(message)s",handlers=[handler])
    logger.addHandler(handler)
    package_to_silence = ['azure', 'langchain','httpx']

    # Stopping root logger in the log file
    for package_name in package_to_silence:
        root_logger = logging.getLogger(package_name)
        root_logger.setLevel(logging.CRITICAL)
        root_logger.propagate = False
    return logger