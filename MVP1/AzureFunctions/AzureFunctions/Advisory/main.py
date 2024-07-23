'''
Main application for advisory plugin
'''
import os
import time
import sys
import logging
import azure.functions as func
from Advisory.utils.advisory import AdvisoryCrawl
from Advisory.utils.logs import create_log
from dotenv import load_dotenv

_ = load_dotenv('./Advisory/config/db.env')

logger = create_log(name="Advisory", level=logging.INFO)
bp_advisory = func.Blueprint()

cron_time = os.getenv('ADVISORY_CHANNEL_CRON')

@bp_advisory.timer_trigger(schedule=cron_time, arg_name="myTimer", run_on_startup=False,
                              use_monitor=False)
async def advisory_news(myTimer: func.TimerRequest) -> None:
    """
    Endpoint to crawl becker for a particuler client and scrape data from individual crawled urls
    Each scraped text is passed to AI model to generate summary, sentiment and matched keyword lists
    params:
        source_name: source from which news is to be extracted; in this case Advisory
        department: department to which source belongs to
        scrape_existing: Flag , True if existing urls are to scraped again else False;
        persist: Flag , True if the scraped content need to be pushed to DB else False
    returns:
        list of dictionary containing news_url,news_summary,sentiment,keywords_list,news_date
    """
    if myTimer.past_due:
        logging.info('The timer is past due!')
    start_time = time.time()

    scrape = AdvisoryCrawl()
    logger.info("Extracting information from Becker Hospitals")
    news_source = "Advisory"
    persist = True
    department_name = "Health systems"
    scrape_existing = False

    final_data=[]
    try:
        json_data = await scrape.get_news_data(department_name=department_name,
                                                scrape_existing=scrape_existing,
                                                persist=persist,source_name=news_source)
        for item in json_data:
            data = {}
            data['news_url'] = item['news_url']
            data['news_summary'] = item['news_summary']
            data['sentiment'] = item['sentiment']
            data['keywords_list'] = item['keywords_list']
            data['news_date'] = item['news_date']
            final_data.append(data)
        logger.info("Data extracted succesfully!")
        final_data = sorted(final_data, key=lambda x: x['news_date'], reverse=True)
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(
            f"Advisory Batch Extraction Completed!  Total Time: {round(total_time, 3)}s")
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in scraping Advisory -Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)

