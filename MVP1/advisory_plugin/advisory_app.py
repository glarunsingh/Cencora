'''
Main application for advisory plugin
'''
import json
import time
import sys
import logging
from typing import Optional,List
from pydantic import BaseModel
import pandas as pd
import uvicorn
# FastAPI imports
from fastapi import FastAPI, BackgroundTasks,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from utils.helper import helper
from utils.advisory_db import AdvisoryDBOPS
from utils.advisory import AdvisoryCrawl
from utils.logs import create_log

logger = create_log(name="Advisory", level=logging.INFO)

#
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


scrape = AdvisoryCrawl()
db_ops = AdvisoryDBOPS()
helper = helper()

class source(BaseModel):
    """BaseModel class for the input to be provided to the Endpoints
    """
    client: Optional[str] = ''
    persist: Optional[bool] = True
    scrape_existing: Optional[bool] = False
    department_name: Optional[str] = "Health"
    source_name: Optional[str] = "advisory"

class db_data(BaseModel):
    """
    BaseModel class for the input to be provided to the DB endpoints
    """
    source_name: str = "advisory"
    start_date : str
    end_date : str

class excel_data(BaseModel):
    """
    BaseModel class for the input to be provided to excel download endpoint
    """
    source_name: str = "advisory"
    dates: List[str]

@app.post("/advisory")
async def advisory_news(search:source):
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
    news_source = search.source_name
    persist = search.persist
    department_name = search.department_name
    scrape_existing = search.scrape_existing
    persist = search.persist

    final_data=[]
    try:
        if news_source.lower() == "advisory":
            json_data = await scrape.get_news_data(department_name=department_name,
                                                   scrape_existing=scrape_existing,
                                                   persist=persist,source_name=news_source.lower())
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
        return (json.dumps({'success':True,'message':"Advisory news articles extracted",
                             "articles":final_data}), 200, {'ContentType':'application/json'})
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in scraping -Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        print(f"Exception {e} occured while scraping")
        return (json.dumps({'success':False,'message':"Advisory news articles failed",
                             "articles":None}), 400, {'ContentType':'application/json'})

@app.post("/advisory_data")
async def get_advisory_data(fetch:db_data):
    """
    Endpoint to extract stored data from DB filtered on timestamp given
    params:
        source_name: source from which news is to be extracted; in this case advisory
    returns:
        list of dictionary containing news_url,news_summary,sentiment,keywords_list,news_date
    """
    try:
        source_name= fetch.source_name
        start_date = fetch.start_date
        end_date = fetch.end_date
       
        data = db_ops.query_items(source_name,start_date,end_date)
        #data = helper.deduplicate_dicts(data,"news_url")
        data = sorted(data, key=lambda x: x['news_date'], reverse=True)
        return (json.dumps({'success':True,'message':"Advisory Data extracted from DB", "articles":data}), 200, {'ContentType':'application/json'})
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading DB data Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        print(f"Exception {e} occured while loading data from DB")
        return (json.dumps({'success':False,'message':"Advisory news articles from DB failed",
                             "articles":None}), 400, {'ContentType':'application/json'})
    
@app.post("/download_excel")
async def download_excel(fetch: excel_data,background_tasks: BackgroundTasks):
    """
    Endpoint to download data in excel
    params:
        dates: list of dates in YYYY-MM format
        source_name: source for which data is to be extracted
    returns:
        data extracted from DB in excel format
    """
    try:
        start_time = time.time()
        input_dates = fetch.dates
        final_data = db_ops.query_excel_items(input_dates,fetch.source_name)
        print(len(final_data))
        if not final_data:
            raise HTTPException(status_code=404, detail="No data found for the given date")

        final_data = sorted(final_data, key=lambda x: x['news_date'], reverse=True)
        df = helper.create_dataframe(final_data)
        f_path,file_name = helper.file_path()

        helper.create_excel(df,f_path)

        end_time = time.time()
        total_time = end_time - start_time
        background_tasks.add_task(helper.delete_file_after_delay, f_path)
        logger.info(f"Excel file created: {f_path} Total Time: {total_time}")

        # Return the file as a response
        return FileResponse(path=f_path, filename=file_name,
                            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'success': False, 'message': "Unable to download excel file"}

if __name__=="__main__":
    uvicorn.run('advisory_app:app',host="127.0.0.1",port=8000, reload=False)
