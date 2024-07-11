import logging
import random
import sys
import time
from datetime import datetime, timedelta
#import azure.functions as func
import os
from dotenv import load_dotenv
import asyncio

from utils.logs import create_log
from utils.cosmos_function import HIMSSDBOPS
from utils.himss_scraper import get_news_items, extract_news_content
from utils.himss_data_extraction import himss_extraction

_ = load_dotenv('./config/db.env')

logger = create_log(name="HIMSS", level=logging.INFO)

async def himss_scrapping_function():
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
    if today_date.date == 1:
        one_day_ago = today_date - timedelta(days=1)
        month_list.append(one_day_ago.month)
        year_list.append(one_day_ago.year)

    content = ""

    success_cnt = 0
    failure_cnt = 0
    data = []
    new_data = {}
    
    #get the list of key words
    key_list = db_ops.query_keyword_list(department_name=department)
    
    data =  himss_extraction(key_list=key_list)
    print(data)

    # call the extracted function
    # pass the keywords, url, hash it and return the data.
    # upload the information in to the database


####################################################################
# Define an asynchronous function to call the scrapping function
async def main():
    await himss_scrapping_function()

# Run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())
