"""
Main app for definitive
"""
import os
import sys

import logging
import azure.functions as func
from Definitive.utils.data_extractor import DataExtractor
from Definitive.utils.definitive_db import DefinitiveDBOPS, DefinitiveClientDBOPS, ConfigDetails
from config import session_key_vault

logger = logging.getLogger(__name__)

bp_definitive = func.Blueprint()

cron_time = os.getenv('DEFINITIVE_CHANNEL_CRON')

@bp_definitive.timer_trigger(schedule=cron_time, arg_name="myTimer", run_on_startup=False,
                             use_monitor=False)
async def definitive_data_extract(myTimer: func.TimerRequest):
    """
    End point to pull data from definitive api and save to DB if persist is true
    """
    if myTimer.past_due:
        logging.info('The timer is past due!')
    try:
        session_key_vault.get_all_values()
        persist = True

        final_data = []
        dbops = DefinitiveDBOPS()
        client_db = DefinitiveClientDBOPS()
        config = ConfigDetails()

        map_title = config.get_config('Definitive', 'element_titles')
        logger.info(f"Element Titles:\t{map_title}")
        expand = config.get_config('Definitive', 'elements')
        logger.info(f"Expand Elements:\t{expand}")
        client_list = client_db.query_clients()
        client_ids = [(item['client_name'], item['client_id']) for item in client_list]
        # print(f"client_ids : {client_ids}")

        for client_name, client_id in client_ids:
            logger.info(f"Extracting data for client {client_id},{client_name}")
            extract_data = DataExtractor(client_id, map_title, expand)
            extracted_dict = extract_data.extract_all_elemets()
            extracted_dict['source_name'] = "Definitive"
            extracted_dict['client_name'] = client_name
            extracted_dict['client_id'] = str(client_id)
            final_data.append(extracted_dict)
            if persist:
                dbops.upsert_items([extracted_dict])
                logger.info(f"Data upserted for client id {client_id}")
            logger.info(f"Data extracted for client {client_id},{client_name}")
        logger.info("Definitive data extraction completed")
        #return {"status": "success", "data": final_data}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading DB data Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        #print(f"Exception {e} occurred while loading data from DB")
        #return {'status': "failed", 'message': "Data extraction failed", "data": []}
