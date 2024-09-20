# Importing the env variables
from dotenv import load_dotenv

_ = load_dotenv()

from config import session_key_vault
from config import logger_setup
session_key_vault.get_all_values()

# Importing logs
import logging
import os
from logging import Logger

logging.basicConfig(level=logging.INFO)
logger = logger_setup.create_log(level=logging.INFO)
logger.propagate = True

logger.info("starting function app")
import azure.functions as func
from DrugChannel.main import bp_drugchannel
from BeckerHospitalReview.main import bp_beckerhospital
from Advisory.main import bp_advisory
from Definitive.main import bp_definitive
from HIMSS.himss import bp_himss
from BingNews.main import bp_bingnews
from Bloomberg.main import bp_bloomberg
from AzureAISearch.main import bp_azure_ai_search_indexer_pipeline

app = func.FunctionApp()
app.register_blueprint(bp_drugchannel)
app.register_blueprint(bp_beckerhospital)
app.register_blueprint(bp_advisory)
app.register_blueprint(bp_definitive)
app.register_blueprint(bp_himss)
app.register_blueprint(bp_bingnews)
app.register_blueprint(bp_bloomberg)
app.register_blueprint(bp_azure_ai_search_indexer_pipeline)
