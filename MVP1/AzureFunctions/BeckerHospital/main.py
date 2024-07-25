"""
Main application for becker review hospital plugin
"""
import os
import random

import time
import sys
import logging

import azure.functions as func
from BeckerHospital.utils.becker_db import ClientDBOPs, KeywordDBOPs
from BeckerHospital.utils.becker_hospital import BeckerCrawl
from BeckerHospital.utils.logs import create_log
from dotenv import load_dotenv

_ = load_dotenv('./BeckerHospital/config/db.env')

logger = create_log(name="Becker_Hospital", level=logging.INFO)
bp_beckerhospital = func.Blueprint()

cron_time = os.getenv('BECKER_CHANNEL_CRON')


@bp_beckerhospital.timer_trigger(schedule=cron_time, arg_name="myTimer", run_on_startup=False,
                                 use_monitor=False)
async def becker_hospital_scrapping_function(myTimer: func.TimerRequest) -> None:
    """
    Endpoint to crawl becker for a particular client and scrape data from individual crawled urls
    Each scraped text is passed to AI model to generate summary, sentiment and matched keyword lists
    params:
        source_name: source from which news is to be extracted; in this case Becker review hospital
        client: search keyword or client name for which data is to be extracted
        duration: Optional ,default:all
        department: department to which source belongs to
        scrape_existing: Flag , True if existing urls are to scraped again else False;
        persist: Flag , True if the scraped content need to be pushed to DB else False
    returns:
        list of dictionary containing news_url,news_summary,sentiment,keywords_list,news_date
    """
    if myTimer.past_due:
        logging.info('The timer is past due!')
    start_time = time.time()

    scrape = BeckerCrawl()
    keyword_db_ops = KeywordDBOPs()
    client_db = ClientDBOPs()

    logger.info("Extracting information from Source Becker Hospital Review")

    news_source = "Becker Hospital Review"
    duration = "all"
    department_name = "all"
    scrape_existing = False 
    persist = True

    final_data = []
    try:
        # querying the keywords
        k_list = keyword_db_ops.query_keyword_list(department_name)
        duration_l = ["all", "start=20", "start=40", "start=60", "start=80", "start=100", "start=120", "start=140",
                      "start=160", "start=180", "start=200", "start=220", "start=240", "start=260", "start=280",
                      "start=300"]
        # Querying the client name
        client_list = client_db.query_client(department_name)
        # client_list = ['Advent Health']  ########################
        for client_name in client_list:
            sleep_time = random.randint(15, 25)
            logger.info(f"Going to sleep to avoid blocking for {sleep_time}s")
            time.sleep(sleep_time)
            logger.info(f"Starting Scrapping for client {client_name}")
            # for duration in duration_l:
            json_data = await scrape.becker_crawling(client_name, duration, k_list, scrape_existing, persist,
                                                     department_name, source_name=news_source)
            if json_data:
                final_data.extend(json_data)
        logger.info("Data extracted successfully!")
        final_data = sorted(final_data, key=lambda x: x['news_date'], reverse=True)
        # logger.info(f"Final:\n{final_data}")#####
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Batch Extraction Completed!  Total Time: {round(total_time, 3)}s")
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in scraping Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
