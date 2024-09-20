import logging
import sys
import time

import azure.functions as func

from AzureAISearch.utils.helpers import AI_Search
from config import session_key_vault

logger = logging.getLogger(__name__)
bp_azure_ai_search_indexer_pipeline = func.Blueprint()

ai_search=AI_Search()

@bp_azure_ai_search_indexer_pipeline.route(route="azure_ai_pipeline", methods=["POST"],
                                           auth_level=func.AuthLevel.ANONYMOUS)
async def azure_ai_search_indexer_pipeline(req: func.HttpRequest) -> func.HttpResponse:

    try:
        #print(req)
        req_body=req.get_json()
        triggered_by=req_body.get('triggered_by')
        logger.info("******************************************************************************************")
        logger.info(f"Starting Azure AI Search Indexer Pipeline  triggered by {triggered_by}")

        session_key_vault.get_all_values()
        ai_search.index_data_to_azure_ai_service(triggered_by)
        return func.HttpResponse("success",status_code=200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error running the Azure AI Search Indexer Pipeline. Line No: {exc_tb.tb_lineno}"
                       f"  Error: {str(e)}", stack_info=True)
        return func.HttpResponse("failure",status_code=500)
