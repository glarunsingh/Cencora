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

from utils.cosmos_function import DrugChannelDBOPS
from utils.excel_functions import  ExcelFunc
from utils.extract_article_content import extract_content_dc
from utils.get_article_list import get_articles_list_dc
from utils.logs import create_log
from utils.url_parameters import url_headers

logger = create_log(name="Drug_Channel", level=logging.INFO)

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

db_ops = DrugChannelDBOPS()
exc_func=ExcelFunc()


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
        if not self.payload:
            raise ValueError("Pass data to parse")
        for date in self.payload:
            year, month = date.split('-')
            year_int = int(year)
            month_int = int(month)
            if not re.match(r"^\d{4}-\d{2}$", date):
                raise ValueError("Date must be in format 'YYYY-MM'")
            if month_int not in range(1, 13):
                raise ValueError("Month out of range")
            if (year_int == datetime.now().year and month_int > datetime.now().month) or year_int > datetime.now().year:
                raise ValueError("Month and year should not be of future")
            if year_int == 2006 and month_int < 5:
                raise ValueError("Data not available for the older dates")
        return self


@app.post("/drug_channel")  #get file path
async def batch_processing_scrapping_drug_channel_data(inputs: dc_inputs):
    start_time = time.time()
    month = inputs.month
    year = inputs.year
    use_db = inputs.use_db
    use_llm = inputs.use_llm_scrapping
    department = inputs.department
    content = ""

    success_cnt = 0
    failure_cnt = 0
    data = []
    new_data = {}

    logger.info("Extracting information from drug channels")
    try:
        sorted_result = await get_articles_list_dc(month=month, year=year, headers=url_headers(), use_llm=use_llm)
        # print(sorted_result, end="\n\n\n")

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
            content, sum_key_sent = await extract_content_dc(url=item['url'], date=item['date'], headers=url_headers(),
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
            f"Batch Extraction Completed!  Total Time: {total_time}s Success: {success_cnt} Failure: {failure_cnt}")

        return ({'success': True, 'message': "Drug Channels articles extracted and uploaded successfully",
                 "data": final_data})

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return ({'success': False, 'message': "Drug Channels articles extraction failed",
                 "data": []})


@app.post("/fetch_dc_data")
async def read_drug_channel_data(fetch: dc_read):
    try:
        start_time = time.time()
        payload = fetch.payload
        final_data = []
        logger.info(f"Querying! {payload}")
        final_data = db_ops.query_items(input_date=payload)
        # for input_date in payload:
        #     logger.info(f"Querying! {input_date}")
        #     query_data = await query_items(input_date=input_date)
        #     final_data.extend(query_data)
        final_data = sorted(final_data, key=lambda x: x['news_date'], reverse=True)
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Data Extraction Completed!  Total Time: {total_time}")
        return {'success': True, 'message': "Data extracted for Drug Channel from DB", "data": final_data}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return ({'success': False, 'message': "Drug Channels articles extraction failed",
                 "data": []})


@app.post("/download_excel")
async def download_excel(fetch: dc_read, background_tasks: BackgroundTasks):
    try:
        start_time = time.time()
        payload = fetch.payload
        final_data = []
        logger.info(f"Querying! {payload}")
        final_data = db_ops.query_items(input_date=payload, excel=True)

        if not final_data:
            raise HTTPException(status_code=404, detail="No data found for the given date")

        final_data = sorted(final_data, key=lambda x: x['news_date'], reverse=True)
        df = exc_func.create_dataframe(final_data)
        f_path, file_name = exc_func.file_path()
        exc_func.create_excel(df, f_path)
        end_time = time.time()
        total_time = end_time - start_time
        background_tasks.add_task(exc_func.delete_file_after_delay, f_path)
        logger.info(f"Excel file created: {f_path} Total Time: {total_time}")

        # Return the file as a response
        return FileResponse(path=f_path, filename=file_name,
                            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except HTTPException as http_exc:
        logger.error(f"HTTPException: {http_exc}", stack_info=True)
        raise http_exc

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        raise HTTPException(status_code=500, detail="Error creating excel file")
        # return {'success': False, 'message': "Unable to download Excel file"}


if __name__ == "__main__":
    uvicorn.run('app:app', host="127.0.0.1", port=8000, reload=False)
