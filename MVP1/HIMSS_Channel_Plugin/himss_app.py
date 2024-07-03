import os
import logging
import random
import re
import sys
import time
from datetime import datetime
from typing import Optional, List, Literal

import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from utils.cosmos_function import HIMSSDBOPS
#from utils.excel_functions import  ExcelFunc
#from utils.extract_article_content import extract_content_dc
#from utils.get_article_list import get_articles_list_dc
from utils.himss_scraper import get_news_items, extract_news_content
from utils.save_json_format import save_news_data
from utils.logs import create_log
from utils.url_parameters import url_headers

logger = create_log(name="HIMSS", level=logging.INFO)

origins = [
    "http://localhost:8000",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:4700",
    "http://localhost:4700"
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

failure_count = 0
total_count = 0

db_ops = HIMSSDBOPS()
#exc_func=ExcelFunc()

class dc_inputs(BaseModel):
    month: Optional[int] = Field(default=datetime.now().month, ge=1, le=12,
                                 description="Article month.Default is set to present month.")
    year: Optional[int] = Field(default=datetime.now().year, ge=2006, le=datetime.now().year,
                                description="Article year.Default is set to present year.")
    department: Optional[Literal["Health", "Government"]] = Field(default="Health",
                                                                  description="Department Name")
    use_db: Optional[bool] = Field(default=True,
                                   description="Flag to indicate whether to call the database(Fast scrapping if "
                                               "enabled.Default is set to True)")
    use_llm_scrapping: Optional[bool] = Field(default=False,
                                              description="Flag to indicate whether to use LLM to scrape the "
                                                          "content.Default is set to False")

def main():
    url = "https://www.himss.org/news"
    news_items = get_news_items(url)

    news_data = []
    for date, news_link in news_items:
        news_topic_text, content_text = extract_news_content(news_link)
        news_data.append({"news_url": news_link,
                          "news_title":news_topic_text,
                          "news_date":date.strftime('%Y-%m-%d:%H'),
                          "news_content":content_text,
                          "news_summary":"",
                          "sentiment":"",
                          "keywords_list":""
                          })
        
    temp_folder_path = os.path.join(os.getcwd(), "temp")
    if not os.path.exists(temp_folder_path):
        os.makedirs(temp_folder_path)

    json_file_path = os.path.join(temp_folder_path,"himss_news_data.json")
    save_news_data(news_data, json_file_path)

    print(f'News data saved to {json_file_path}')

if __name__ == "__main__":
    main()