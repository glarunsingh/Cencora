"""
Main application for Bing News Extraction
"""
import ast
import asyncio
import time
import sys
import os
import azure.functions as func

from AzureAISearch.utils.helpers import AI_Search
from BingNews.utils import database
from BingNews.utils import bing_crawler
from datetime import datetime, timedelta
import logging
from config import session_key_vault
session_key_vault.get_all_values()

logger = logging.getLogger(__name__)
bp_bingnews = func.Blueprint()

bing_news_db = database.Bing_News_DB()
cron_time = os.getenv('BING_NEWS_CRON')

@bp_bingnews.timer_trigger(schedule=cron_time, arg_name="myTimer", run_on_startup=False,
                           use_monitor=False)
async def bing_news_scrapping(myTimer: func.TimerRequest) -> None:
    """
    Endpoint to crawl Bing news for a given client list using API and scrape data for each url.
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
    if myTimer.past_due:
        logging.info('The timer is past due!')

    #final_data = []
    try:
        session_key_vault.get_all_values()
        #department_list= ["Health systems", "Government sales", "Triose"]
        logger.info(f"Starting Bing News crawling for all department ")
        #department_name = "Health systems"
        source_name = "Bing News"
        client_name = ["All"]
        minDate = (datetime.now().date() - timedelta(days=3)).strftime(
            "%Y-%m-%d")  # "2024-07-15" #replace with today's date
        write_db = True
        location = "US"

        start_time = time.time()
        news_data = bing_crawler.BingCrawl(source_name=source_name, minDate=minDate, location=location,
                                            store_db=write_db)

        if client_name[0] == "All":
            client_list = bing_news_db.query_client_list()
        else:
            client_list = []
            for item in client_name:
                client_list.append({'client_name': item, 'search_term': f'"{item.strip()}"'})

        for client in client_list:
            logger.info(f"Starting Bing News Extraction for {client['search_term']}")
            news_data.url_processing(client_name=client['client_name'], search_term=client['search_term'])
            #final_data.extend(news_data.all_articles_info)
        logger.info(f"Completed Bing News crawling for all departments ")
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Batch Extraction Completed!  Total Time: {round(total_time, 3)}s")
        logger.info(f"Bing News extraction completed for given client list")

        ## Trigger Azure AI search pipeline
        ai_index_pipeline_request = asyncio.create_task(AI_Search.async_trigger_http_function("Bing News Function"))

        # return ({'success': True,'message': "Bing News extraction completed","data": final_data})
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        print(f"Exception {e} occured")
        # return ({'success': False,'message': "Bing News extraction failed","data": []})

