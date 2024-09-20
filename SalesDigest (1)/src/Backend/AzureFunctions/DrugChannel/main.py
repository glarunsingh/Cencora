import asyncio
import logging
import random
import sys
import time
from datetime import datetime, timedelta
import azure.functions as func
import os

from AzureAISearch.utils.helpers import AI_Search
from DrugChannel.utils.cosmos_function import DrugChannelDBOPS
from DrugChannel.utils.extract_article_content import extract_content_dc
from DrugChannel.utils.get_article_list import get_articles_list_dc
from DrugChannel.utils.url_parameters import url_headers
from config import session_key_vault

logger = logging.getLogger(__name__)
bp_drugchannel = func.Blueprint()

failure_count = 0
total_count = 0
cron_time = os.getenv('DRUG_CHANNEL_CRON')


@bp_drugchannel.timer_trigger(schedule=cron_time, arg_name="myTimer", run_on_startup=False,
                              use_monitor=False)
async def drug_channel_scrapping_function(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
    session_key_vault.get_all_values()
    start_time = time.time()
    logger.info("Extracting information from drug channels")
    db_ops = DrugChannelDBOPS()

    # get current month and year
    today_date = datetime.now()

    # Function Arguments
    month_list = [today_date.month]
    year_list = [today_date.year]
    use_db = True
    use_llm = False
    department = None

    # to avoid missing the article published on last date of month
    if today_date.date == 1:
        one_day_ago = today_date - timedelta(days=1)
        month_list.append(one_day_ago.month)
        year_list.append(one_day_ago.year)

    content = ""

    success_cnt = 0
    failure_cnt = 0
    data = []
    new_data = {}
    try:
        for month, year in zip(month_list, year_list):
            sorted_result = await get_articles_list_dc(month=month, year=year, headers=url_headers(), use_llm=use_llm)
            if use_db:
                item_list, url_list = db_ops.query_urls(month=month, year=year)
                filtered_item = [item for item in sorted_result if item['url'] not in url_list]
                key_list = db_ops.query_keyword_list(department_name=department)
            else:
                filtered_item = sorted_result
                item_list = []
                key_list = []

            for item in filtered_item:
                logger.info(f"Drug channel URL - {item['url']}")
                # Sleeping to avoid blocking
                sleep = random.randint(5, 16)
                logger.info(f"Script put to sleep for {sleep}s")
                time.sleep(sleep)
                content, sum_key_sent = await extract_content_dc(url=item['url'], date=item['date'],
                                                                 headers=url_headers(),
                                                                 use_llm=use_llm, key_list=key_list)

                if content is not None and sum_key_sent is not None:
                    new_data = {
                        "source_name": "Drug Channel",
                        "client_name": "",
                        "news_url": item['url'],
                        "news_title": item['title'],
                        "news_date": item['date'],
                        "news_content": content,
                        "news_summary": sum_key_sent.summary_schema,
                        "keywords_list": sum_key_sent.keyword_schema,
                        "sentiment": sum_key_sent.sentiment_schema,
                    }
                    success_cnt += 1
                    data.append(new_data)
                else:
                    failure_cnt += 1

            if use_db and data != []:
                await db_ops.upsert_data(data)
        data.extend(item_list)  # Added the DB data to the existing data
        final_data = sorted(data, key=lambda x: x['news_date'], reverse=True)
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(
            f"Batch Extraction Completed!  Total Time: {round(total_time, 3)}s Success: {success_cnt} "
            f"Failure: {failure_cnt}")

        ## Trigger Azure AI search pipeline
        ai_index_pipeline_request =asyncio.create_task(AI_Search.async_trigger_http_function("Drug Channel Function"))

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Unhandled Exception: Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
