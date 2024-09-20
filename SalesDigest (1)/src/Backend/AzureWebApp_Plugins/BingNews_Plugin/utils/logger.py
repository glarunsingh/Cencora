# Set up logging to write to a file
import logging
import os
from logging.handlers import RotatingFileHandler

from logging import Logger
from opencensus.ext.azure.log_exporter import AzureLogHandler

from config.key_vault import key_vault
secret_value = key_vault()

APPLICATION_INSIGHTS_STRING_WEBTOOLS = secret_value.get_secret('APPLICATION-INSIGHTS-STRING-WEBTOOLS') #os.environ['BING_NEWS_URL']

#APPLICATION_INSIGHTS_STRING_WEBTOOLS= "InstrumentationKey=1d1184e2-70e7-4a30-a23b-b14afd5b9562;IngestionEndpoint=https://eastus2-3.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus2.livediagnostics.monitor.azure.com/;ApplicationId=7fcf337d-bc52-4417-88cd-61565b6739ae"
def create_log(level):

    logger = logging.getLogger()
    handler = AzureLogHandler(connection_string = APPLICATION_INSIGHTS_STRING_WEBTOOLS)
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

def create_log1(name: str, level):
    """function for logging backend activities"""
    if not os.path.exists("./logs/"):
        os.makedirs("./logs/",exist_ok=True)
    handler =RotatingFileHandler("./logs/log.log", maxBytes=2097152, backupCount=20)
    logging.basicConfig(level=level,datefmt="%Y-%m-%d %H:%M:%S",
                        format="%(asctime)s  %(filename)s  Line: %(lineno)d  %(levelname)s  Function_Name: %("
                               "funcName)s  %(message)s",handlers=[handler])
    logger = logging.getLogger(name)

    package_to_silence = ['azure', 'langchain','httpx']

    # Stopping root logger in the log file
    for package_name in package_to_silence:
        root_logger = logging.getLogger(package_name)
        root_logger.setLevel(logging.CRITICAL)
        root_logger.propagate = False

    return logger