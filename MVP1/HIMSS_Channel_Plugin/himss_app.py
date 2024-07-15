import logging
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import asyncio
import json
import sys

from utils.logs import create_log
from utils.cosmos_function import HIMSSDBOPS
from utils.himss_data_extraction import himss_extraction
from utils.summarizer import llm_content_sum_key_sent

#from azure.functions import func
#app = func.FunctionApp()

_ = load_dotenv('./config/db.env')

logger = create_log(name="HIMSS", level=logging.INFO)

failure_count = 0
total_count = 0
cron_time=os.getenv('HIMSS_CRON')
#@app.timer_trigger(schedule=cron_time, arg_name="myTimer", run_on_startup=False,use_monitor=False) 

async def himss_scrapping_function():#myTimer: func.TimerRequest) -> None:
    #if myTimer.past_due:
    #    logging.info('The timer is past due!')
    start_time = time.time()
    logger.info("Extracting information from HIMSS website")

    db_ops = HIMSSDBOPS()

    # get current month and year
    today_date = datetime.now()

    # Function Arguments
    month_list = [today_date.month]
    year_list = [today_date.year]
    use_db = True
    use_llm = False
    department = None

    # to avoid missing the article published on last date of month
    if today_date.day == 1:
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
            extracted_data = await himss_extraction()
            if use_db:
                item_list, url_list = db_ops.query_urls(month=month, year=year)
                #filtered_item = [item for item in extracted_data if item['url'] not in url_list]
                filtered_item = [item for item in extracted_data if 'news_url' in item and item['news_url'] not in url_list]

                key_list = db_ops.query_keyword_list(department_name=department)

                # get the list of keywords
                #key_list = db_ops.query_keyword_list(department_name=department)
            else:
                filtered_item = extracted_data
                item_list = []
                key_list = []
        

        # Extract data from HIMSS
        processed_data = []
        
        for item in extracted_data:
            try:
                # Process each item with LLM
                llm_result = await llm_content_sum_key_sent(item['news_content'], item['news_url'], key_list)

                processed_item = {
                    "news_url": item['news_url'],
                    "news_title": item['news_title'],
                    "news_date": item['news_date'],
                    "news_content": item['news_content'],
                    "news_summary": llm_result.summary_schema,
                    "sentiment": llm_result.sentiment_schema,
                    "keywords_list": llm_result.keyword_schema,
                    "source_name": "HIMSS"
                }
                
                processed_data.append(processed_item)
                logger.info(f"Processed item: {item['news_url']}")
            except Exception as e:
                logger.error(f"Error processing item {item['news_url']}: {str(e)}")
        
        #uploading the data in the cosmos db
        await db_ops.upsert_data(processed_data)

        # Save processed data as JSON in temp folder
        temp_folder = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_folder, exist_ok=True)
        json_file_path = os.path.join(temp_folder, f"himss_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        try:
            with open(json_file_path, 'w') as json_file:
                json.dump(processed_data, json_file, indent=4)
            logger.info(f"Processed data saved to {json_file_path}")
        except IOError as e:
            logger.error(f"Error saving JSON file: {str(e)}")

        end_time = time.time()
        logger.info(f"Total execution time: {end_time - start_time} seconds")

        return processed_data
    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Unhandled Exception: Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
    

# Define an asynchronous function to call the scrapping function
async def main():
    await himss_scrapping_function()

# Run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())