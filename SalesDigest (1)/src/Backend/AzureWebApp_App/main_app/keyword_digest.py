"""
Script for the APIss of the keyword Digest Page
"""
import asyncio
import sys
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from pydantic import BaseModel, field_validator, model_validator, ValidationError, Field, AnyUrl

from Authentication.auth import validate_user,websocket_validate_user
from main_app.utils.azure_ai_search import Keyword_Summarizer, Azure_AI_Search
from main_app.utils.digest_db import KeywordDBOPs, ClientDBOPs, SourceDBOPs, DigestDBOPS
from main_app.utils.helper import helper
from fastapi.responses import FileResponse


import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/keyword_digest',
                   tags=['Keywords Digest'])
db_ops = DigestDBOPS()
client_db = ClientDBOPs()
keyword_db = KeywordDBOPs()
source_db = SourceDBOPs()
helper = helper()
ai_search = Azure_AI_Search()

class keyword_payload(BaseModel):
    """
    Pydantic class to validate the payload for keyword details
    """
    user_email: str
    department: str


@router.post("/fetch_keywords", tags=['Keywords Digest'])
async def get_keyword_details(fetch: keyword_payload, token_details: dict = Depends(validate_user)):
    """
        This function fetches keyword details from the database and returns them as response.

        Args:
            fetch (keyword_payload): The payload containing user email and department.
            token_details (dict): The user's token details.

        Returns:
            dict: A dictionary with the status, message, and data.
    """
    try:
        keyword_list = keyword_db.query_keyword_list(fetch.department)

        # Top 5 keywords based on count
        top_keywords= keyword_list[:5]
        keyword_list.sort()
        data = {"keywords": keyword_list, "top_keywords": top_keywords}
        return {'status': "success", 'message': "Data Sent Successfully", "data": data,
                "user_details": token_details}
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading DB data Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'status': "failed", 'message': "Unable to fetch data", "data": []}


class keyword_digest_payload(BaseModel):
    """
    Pydantic class to validate the payload for keyword search details
    """
    search_text: str
    start_date: str
    end_date: str
    department: str
    pageInformation: str =Field(description="Page from where it is called",default="keyword_digest_page-News Articles")
    emp_id: str

    @field_validator("start_date", "end_date")
    def validate_dates(cls, value: str) -> str:
        """
        Field validator to validate the date format.
        The date format should be YYYY-MM-DD.
        """
        try:
            # validate date format
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                "Incorrect date format, should be YYYY-MM-DD"
            ) from ValueError
        return value

    @model_validator(mode="after")
    def validate_dates_range(self):
        """
        Validates the date range.

        Ensures that the start date is less than or equal to the end date.
        """
        if self.start_date > self.end_date:
            raise ValueError(
                "Start date should be less than or equal to end date. "
                f"Start date: {self.start_date}, End date: {self.end_date}"
            )
        return self


@router.post("/get_search_data", tags=['Keywords Digest'])
async def get_search_data(fetch: keyword_digest_payload,background_tasks: BackgroundTasks, token_details: dict = Depends(validate_user)):
    """
        This function fetches keyword details from the database and returns them as response.

        Args:
            fetch (keyword_payload): The payload containing user email and department.
            token_details (dict): The user's token details.
            background_tasks (BackgroundTasks): The background tasks to increment the keyword count in the database
        Returns:
            dict: A dictionary with the status, message, and data.
    """
    try:
        search_text = fetch.search_text
        department = fetch.department
        start_date = fetch.start_date
        end_date = fetch.end_date
        pageInformation = fetch.pageInformation
        emp_id=fetch.emp_id
        department_flag = True # flag to filter news based on the department

        if department_flag:
            # get the department sources
            source_list = source_db.query_source_for_department(department)
            if not source_list:
                return {'status': "failed", 'message': "No sources found for the department", "data": []}

            # get the department clients
            client_list = client_db.query_client(department)
            if not client_list:
                return {'status': "failed", 'message': "No clients found for the department", "data": []}

        else:
            client_list=[]
            source_list=[]
        k_search = Keyword_Summarizer(department=department,search_query=search_text,
                                       start_date=start_date, end_date=end_date, client_list=client_list)
        # get the search results of keyword based on the client list and date range
        search_results = k_search.get_search_results(source_list=source_list,
                                                      department_flag=department_flag,
                                                      top_percentage_results_flag=True)
        if not search_results:
            return {'status': "failed", 'message': f"No results found for the keyword {search_text}", "data": []}
        results= await k_search.refine_search_results(search_results,emp_id,pageInformation)

        news_results = {'news_articles': results}
        logger.info("News articles fetched successfully")

        # Adding background task to increment keyword count
        background_tasks.add_task(keyword_db.increment_keyword_count, keyword_name=search_text,
                                  department_name=department)

        return {'status': "success", 'message': "Data Sent Successfully", "data": news_results,
                "user_details": token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading Keyword search results Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'status': "failed", 'message': "Unable to fetch data", "data": []}


class keyword_digest_summary_payload(BaseModel):
    """
    Pydantic class to validate the payload for keyword search summary details
    """
    search_text: str
    start_date: str
    end_date: str
    department: str

    @field_validator("start_date", "end_date")
    def validate_dates(cls, value: str) -> str:
        """
        Field validator to validate the date format.
        The date format should be YYYY-MM-DD.
        """
        try:
            # validate date format
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                "Incorrect date format, should be YYYY-MM-DD"
            ) from ValueError
        return value

    @model_validator(mode="after")
    def validate_dates_range(self):
        """
        Validates the date range.

        Ensures that the start date is less than or equal to the end date.
        """
        if self.start_date > self.end_date:
            raise ValueError(
                "Start date should be less than or equal to end date. "
                f"Start date: {self.start_date}, End date: {self.end_date}"
            )
        return self


@router.post("/get_keyword_summary", tags=['Keywords Digest'])
async def get_keyword_summary_async(fetch: keyword_digest_summary_payload, token_details: dict = Depends(validate_user)):
    """
        This function fetches keyword details from the database and returns them as response.

        Args:
            fetch (keyword_payload): The payload containing user email and department.
            token_details (dict): The user's token details.
            background_tasks (BackgroundTasks): The background tasks to increment the keyword count in the database
        Returns:
            dict: A dictionary with the status, message, and data.
    """
    try:
        search_text = fetch.search_text
        department = fetch.department
        start_date = fetch.start_date
        end_date = fetch.end_date
        department_flag = True # flag to filter news based on the department

        # get the department sources
        source_list = source_db.query_source_for_department(department)
        print(source_list)
        if not source_list:
            return {'status': "failed", 'message': "No sources found for the user", "data": []}

        # get the department clients
        client_list = client_db.query_client(department)
        print(len(client_list))
        if not client_list:
            return {'status': "failed", 'message': "No clients found for the user", "data": []}


        # get the search results of keyword based on the client list and date range
        k_search = Keyword_Summarizer(department=department,search_query=search_text,
                                       start_date=start_date, end_date=end_date, client_list=client_list)
        # get the search results of keyword based on the client list and date range
        search_results = k_search.get_search_results(source_list=source_list,
                                                      department_flag=department_flag,
                                                      top_percentage_results_flag=True)

        if not search_results:
            return {'status': "failed", 'message': f"No results found for the keyword {search_text}", "data": []}

        consolidated_summary_task = asyncio.create_task(k_search.consolidated_summary())
        insights_summary_task = asyncio.create_task(k_search.insights_summary())
        report_summary_task = asyncio.create_task(k_search.report_summary())


        results = await asyncio.gather(report_summary_task,consolidated_summary_task,insights_summary_task)

        news_results = {'market_report': results[0], 'consolidated_summary': results[1], 'key_insights': results[2]}
        logger.info("News articles fetched successfully")

        return {'status': "success", 'message': "Data Sent Successfully", "data": news_results,
                "user_details": token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading Keyword search results Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'status': "failed", 'message': "Unable to fetch data", "data": []}


class KeywordDigestExcelPayload(BaseModel):
    """"
    Pydantic class to validate the payload for keyword search Excel download
    """
    url_list:List[AnyUrl]
    department: str

@router.post("/download_searched_news_excel")
async def download_searched_news_excel(fetch: KeywordDigestExcelPayload,background_tasks: BackgroundTasks,
                                       token_details: dict = Depends(validate_user)):
    """
        Download searched news as an Excel file.
        This endpoint takes a list of URLs and a department as input,
        and returns an Excel file containing the searched news.

        Args:
        - fetch (KeywordDigestExcelPayload): Payload containing URL list and department.
        - background_tasks (BackgroundTasks): Background tasks for created excel to be deleted after a while.
        - token_details (dict): User token details.

        Returns:
        - FileResponse: Excel file containing searched news.
        """
    try:

        url_list = [str(url) for url in fetch.url_list]

        # getting clients and sources based on the department
        client_list= client_db.query_client(fetch.department)
        source_list = source_db.query_source_for_department(fetch.department)

        #If either of the two source or client lists is empty, raise an exception
        if not source_list or not client_list:
            return {'status': "failed", 'message': "No sources or clients found", "data": {}}

        #get the data from the database based on the url,client and source
        data = db_ops.query_items_from_url_list(url_list,client_list,source_list)
        if not data:
            return {'status': "failed", 'message': "No data found", "data": {}}

        # replace empty client name with Others
        for item in data:
            if item['client_name'].strip() == "":
                item['client_name'] = "Others"

        deduplicate_data = helper.deduplicate_dicts(data, "news_url")
        df = helper.create_dataframe(deduplicate_data)

        #Create Excel file

        f_path, file_name = helper.file_path(name_initial="Keyword_Digest_")
        helper.create_excel(df, f_path)

        #background task to delete the created Excel file after a while
        background_tasks.add_task(helper.delete_file_after_delay, f_path)
        logger.info(f"Excel file created: {f_path}")
        return FileResponse(path=f_path, filename=file_name,
                            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'status': "failed", 'message': "Unable to download excel file", "data": {}}


@router.websocket("/get_search_data_websocket")
async def get_websockets_keywords_digest_page_data(websocket: WebSocket,token_details: dict = Depends(websocket_validate_user)): #,token_details: dict = Depends(validate_user)
    await websocket.accept()
    logger.info("Client connected")
    #while True:
    data = await websocket.receive_json()
    logger.info(f"Data received from client")
    error_response_schema = {
        "tab_name": "Error",
        "body": {
            "data": [],
            "success": False,
            "message": "Failed to get data"
        }
    }

    try:
        # validate the data
        validation = keyword_digest_payload(**data)
        # get the department clients
        client_list= client_db.query_client(data['department'])
        if not client_list:
            error_response_schema["body"]["message"] ="No clients found"
            logger.info("No clients found")
            await websocket.send_json(error_response_schema)
            return
        # get the search results of keyword based on the client list and date range
        search_results = ai_search.get_search_results(search_query=data['search_text'],
                                                      start_date=data['start_date'],
                                                      end_date=data['end_date'],
                                                      client_list=client_list)

        if not search_results:
            error_response_schema["body"]["message"] ="No Search results found"
            logger.info("No Search results found")
            await websocket.send_json(error_response_schema)
            return


        news_tile_results = ai_search.refine_search_results(search_results,data['emp_id'])
        if news_tile_results:
            response_schema = {
                "tab_name": "news_articles",
                "body": {
                    "data": news_tile_results,
                    "success": True,
                    "message": "Data Sent Successfully"
                }
            }
        else:
            response_schema = {
                "tab_name": "news_articles",
                "body": {
                    "data": [],
                    "success": False,
                    "message": "No results found"
                }
            }
            logger.info("Error in getting news articles")

        # send the refined search results
        await websocket.send_json(response_schema)

        logger.info("Search results sent successfully")

    except WebSocketDisconnect:
        logger.warning("Client disconnected")

    except ValidationError as e:
        logger.error(f"Validation Error: {str(e)}", stack_info=True)
        await websocket.send_text(str(e))

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in getting search results Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)

        await websocket.send_json(error_response_schema)

    finally:
        await websocket.close()
        logger.info("Websocket closed successfully.")