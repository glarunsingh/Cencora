"""
Main application for Bloomberg News Extraction
"""
import asyncio
import time
import sys
import os
import azure.functions as func

from AzureAISearch.utils.helpers import AI_Search
from Bloomberg.utils import database
from Bloomberg.utils import bloomberg_crawler
from datetime import datetime, timedelta

import logging
from config import session_key_vault
session_key_vault.get_all_values()

logger = logging.getLogger(__name__)
bp_bloomberg = func.Blueprint()

bloomberg_news_db = database.News_DB()
cron_time = os.getenv('BLOOMBERG_NEWS_CRON')

@bp_bloomberg.timer_trigger(schedule=cron_time, arg_name="myTimer", run_on_startup=False,
                        use_monitor=False)
async def bloomberg_news_scrapping(myTimer: func.TimerRequest) -> None:
    """
    Endpoint to crawl Bloomberg news.
    Each scraped text is passed to LLM model to clean content, summary, sentiment,
    matched keyword lists, breaking news and client relevance.
    params:
        source_name: source from which news is to be extracted; in this case 'Bloomberg Government'
        department: department for which news is extracted, default:'Health systems'
        write_db : Flag to indicate whether to store in the database
        
    returns:
        list of dictionary containing news_url, news_content, news_summary, sentiment, keywords_list, news_date
    """
    if myTimer.past_due:
        logging.info('The timer is past due!')

    final_data = []
    try:
        session_key_vault.get_all_values()
        logger.info(f"Starting Bloomberg News Extraction")
        source_name= "Bloomberg Government"
        department_name= "Government sales"
        write_db = True

        start_time = time.time()
        news_data = bloomberg_crawler.BloombergCrawl(source_name=source_name,
                                                    department_name=department_name, store_db=write_db)

        news_data.url_processing()
        final_data.extend(news_data.all_articles_info)
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Completed Bloomberg News Extraction!  Total Time: {round(total_time, 3)}s")

        ## Trigger Azure AI search pipeline
        ai_index_pipeline_request = asyncio.create_task(AI_Search.async_trigger_http_function("Bloomberg Function"))

        # return ({'success': True,'message': "Bloomberg News extraction completed","data": final_data})
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        print(f"Exception {e} occured")
        # return ({'success': False,'message': "Bloomberg News extraction failed","data": []})

