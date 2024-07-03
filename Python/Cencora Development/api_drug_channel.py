import uvicorn
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import re
import json
import random
from random import randint
from pydantic import BaseModel, Field, model_validator, ValidationError, validator
from typing import Optional, List
import time
from fastapi import FastAPI
import ssl
from urllib.error import URLError, HTTPError
from httpcore import ProxyError
from httpx import InvalidURL
import logging
import asyncio
import os
import sys
from dotenv import load_dotenv
import hashlib
import time

from utils.cosmos_function import upsert_data, query_items, query_urls
from utils.extract_article_content import extract_content_dc
from utils.get_article_list import get_articles_list_dc
from utils.logs import create_log
from utils.summarizer import get_summary
from utils.url_parameters import url_headers, read_timeout, dateformat
from azure.cosmos.aio import CosmosClient

logger = create_log(name="Drug_Channel", level=logging.INFO)

app = FastAPI()

failure_count = 0
total_count = 0


class dc_inputs(BaseModel):
    month: Optional[int] = Field(default=datetime.now().month, ge=1, le=12,
                                 description="Article month.Default is set to present month.")
    year: Optional[int] = Field(default=datetime.now().year, ge=2006, le=datetime.now().year,
                                description="Article year.Default is set to present year.")
    use_db: Optional[bool] = Field(default=True,
                                   description="Flag to indicate whether to call the database(Fast scrapping if "
                                               "enabled.Default is set to True)")
    use_llm_scrapping: Optional[bool] = Field(default=False,
                                              description="Flag to indicate whether to use LLM to scrape the "
                                                          "content.Default is set to False")

    @model_validator(mode='after')
    def avoid_future_dates(self):
        if self.year == datetime.now().year and self.month > datetime.now().month:
            raise ValueError("Month and year should not be of future")
        elif self.year == 2006 and self.month < 5:
            raise ValueError("Data not available for the older dates")
        return self


class dc_read(BaseModel):
    payload: List[str]

    @model_validator(mode='after')
    def check_date_format(self):
        for date in self.payload:
            year, month = date.split('-')
            year_int = int(year)
            month_int = int(month)
            if len(year) != 4 or len(month) != 2:
                raise ValueError("Date must be in format 'YYYY-MM'")
            if month_int not in range(1, 13):
                raise ValueError("Month out of range")
            if (year_int == datetime.now().year and month_int > datetime.now().month) or year_int > datetime.now().year:
                raise ValueError("Month and year should not be of future")
            if year_int == 2006 and month_int < 5:
                raise ValueError("Data not available for the older dates")
            return self


# class dc_read(BaseModel):
#     payload: List[DateElement]

@app.post("/drug_channel")  #get file path
async def get_news_content_for_dc(inputs: dc_inputs):
    # To be removed
    #inputs = dc_inputs(**inputs)
    #
    start_time=time.time()
    month = inputs.month
    year = inputs.year
    use_db = inputs.use_db
    use_llm = inputs.use_llm_scrapping
    content = ""

    success_cnt = 0
    failure_cnt = 0

    data_exists = False
    data = []
    new_data = {}
    start_time = time.time()
    ########
    s = []
    con = []
    ########
    logger.info("Extracting information from drug channels")
    try:
        sorted_result = await get_articles_list_dc(month=month, year=year, headers=url_headers(), use_llm=use_llm)
        print(sorted_result, end="\n\n\n")

        if use_db:
            item_list, url_list = await query_urls(month=month, year=year)
            filtered_item = [item for item in sorted_result if item['url'] not in url_list]
        else:
            filtered_item = sorted_result
            item_list = []

        for item in filtered_item:
            logger.info(f"Drug channel URL - {item['url']}")
            # Sleeping to avoid blocking
            sleep = random.randint(5, 16)
            logger.info(f"Script put to sleep for {sleep}s")
            # to be removed
            time.sleep(sleep)
            content, summary = await extract_content_dc(url=item['url'], date=item['date'], headers=url_headers(),
                                                        use_llm=use_llm)
            s.append([item['url'], summary])
            con.append([item['url'], content])

            if content is not None and summary is not None:
                new_data = {
                    "source_name": "Drug Channel",
                    "client_name": "DrugChannel",
                    "news_url": item['url'],
                    "news_title": item['title'],
                    "news_date": item['date'],
                    "news_content": content,
                    "news_summary": summary,
                    "keywords_list": [],
                    "sentiment": '',
                }
                success_cnt+=1
                data.append(new_data)
            else:
                failure_cnt+=1

        # with open('summary.txt', 'w') as f:
        #     for item in s:
        #         f.write(f"{item}\n\n")
        # with open('content.txt', 'w') as f:
        #     for item in con:
        #         f.write(f'{item}\n\n')
        if use_db and data!=[]:
            await upsert_data(data)

        data.extend(item_list)  #Added the DB data to the existing data
        end_time = time.time()
        total_time=end_time-start_time
        logger.info(f"Batch Extraction Completed!  Total Time: {total_time} Success: {success_cnt} Failure: {failure_cnt}")

        return ({'success': True, 'message': "Drug Channels articles extracted and uploaded successfully",
                 "data": data})

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return ({'success': False, 'message': "Drug Channels articles extraction failed",
                 "data": []})


@app.post("/fetch_dc_data")
async def get_dc_data(fetch: dc_read):
    # To be removed
    #fetch = dc_read(**fetch)
    ##
    try:
        start_time=time.time()
        payload = fetch.payload
        final_data = []
        #year = fetch.year
        for input_date in payload:
            logger.info(f"Querying! {input_date}")
            query_data = await query_items(input_date=input_date)
            final_data.extend(query_data)
        final_data = sorted(final_data, key=lambda x: x['news_date'], reverse=True)
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Data Extraction Completed!  Total Time: {total_time}")
        return ({'success': True, 'message': "Data extracted for Drug Channel from DB", "data": final_data})

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return ({'success': False, 'message': "Drug Channels articles extraction failed",
                 "data": []})


if __name__ == "__main__":
    uvicorn.run('app:app', host="127.0.0.1", port=8000, reload=False)

#
# external_data = {
#     'year': 2024,
#     'month': 3,
#     'standalone': True,
#     'use_llm_scrapping': False,
#     'summarize': True
# }
# read_data = {
#     "payload": ["2024-06","2024-03"]
# }
# #data = asyncio.run(get_news_content_for_dc(external_data))
# data = asyncio.run(get_dc_data(read_data))
# print(data)
