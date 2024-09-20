"""
Main application for Becker Hospital Review News Extraction
"""
import ast
import asyncio
import sys
import os
import azure.functions as func
import random
import time

from AzureAISearch.utils.helpers import AI_Search
from BeckerHospitalReview.utils import database
from BeckerHospitalReview.utils import becker_crawler
from datetime import datetime, timedelta
import logging
from config import session_key_vault

logger = logging.getLogger(__name__)
bp_beckerhospital = func.Blueprint()

becker_news_db = database.News_DB()
cron_time = os.getenv('BECKER_CHANNEL_CRON')

@bp_beckerhospital.timer_trigger(schedule=cron_time, arg_name="myTimer", run_on_startup=False,
                                 use_monitor=False)
async def becker_hospital_scrapping_function(myTimer: func.TimerRequest) -> None:
    """
    Endpoint to crawl Becker news for a given client list using API and scrape data for each url.
    Each scraped text is passed to LLM model to clean content, summary, sentiment,
    matched keyword lists, breaking news and client relevance.
    params:
        source_name: source from which news is to be extracted; in this case Bing News, default:'Bing News'
        department: department for which news is extracted, default:'Health systems'
        client: list of search keyword or client name for which data is to be extracted,default:['All']
        minDate: from when news needs to be extracted
        write_db : Flag to indicate whether to store in the database
        location: US , location form which news is extracted;
        
    returns:
        list of dictionary containing news_url, news_content, news_summary, sentiment, keywords_list, news_date
    """
    #final_data = []
    try:
        session_key_vault.get_all_values()

        source_name = "Becker Hospital Review"
        client_name = ["All"] #["Ann & Robert H Lurie Childrens Hospital of Chicago"]
        minDate = (datetime.now().date() - timedelta(days=5)).strftime(
            "%Y-%m-%d")  # "2024-07-15" #replace with today's date
        write_db = True
        location = "US"
        start_time = time.time()
        news_data = becker_crawler.BeckerCrawl(source_name=source_name, minDate=minDate, location=location,
                                             store_db=write_db)

        if client_name[0] == "All":
            client_list = becker_news_db.query_client_list()
        else:
            client_list = []
            for item in client_name:
                client_list.append({'client_name': item, 'search_term': f'"{item.strip()}"'})

        for client in client_list:
            sleep_time = random.randint(15, 25)
            logger.info(f"Going to sleep to avoid blocking for {sleep_time}s")
            time.sleep(sleep_time)
            logger.info(f"Starting Becker News Extraction for {client['search_term']}")
            news_data.url_processing(client_name=client['client_name'], search_term=client['search_term'])
            #final_data.extend(news_data.all_articles_info)
            
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Batch Extraction Completed!  Total Time: {round(total_time, 3)}s")

        ## Trigger Azure AI search pipeline
        ai_index_pipeline_request = asyncio.create_task(AI_Search.async_trigger_http_function("Becker Hospital Review Function"))

        #return ({'success': True,'message': "Becker News extraction completed","data": final_data})
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        #return ({'success': False,'message': "Becker News extraction failed",
        #                    "data": []})
