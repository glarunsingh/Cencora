"""
This file contains all the dependencies API required for the frontend app.
"""
from typing import List, Optional
from pydantic import BaseModel, EmailStr, conlist, Field
import time
import sys

# FastAPI imports
from fastapi import BackgroundTasks, HTTPException, APIRouter, Depends
from fastapi.responses import FileResponse

from Authentication.auth import validate_user
from main_app.utils.helper import helper
from main_app.utils.digest_db import DigestDBOPS, ClientDBOPs, UserDBOPs, SourceDBOPs, DefinitiveClientDBOPS, \
    KeywordDBOPs
from fastapi.responses import JSONResponse
from feedback_page.utils.db_helper import DBOPS

router = APIRouter(prefix='/main_app',
                   tags=['main_app'])

import logging
logger = logging.getLogger(__name__)

db_ops = DigestDBOPS()
user_db = UserDBOPs()
client_db = ClientDBOPs()
sourcedb = SourceDBOPs()
definitiveclientdb = DefinitiveClientDBOPS()
keyword_db = KeywordDBOPs()
helper = helper()
feedback_db = DBOPS()


class db_data(BaseModel):
    """
    BaseModel class for the input to be provided to the DB endpoints
    """
    source_name: List[str]
    client: List[str]
    start_date: str
    end_date: str
    sentiment_list: conlist(str, min_length=1, max_length=3)


class def_data(BaseModel):
    """
    BaseModel class for the input to be provided to the DB endpoints
    """
    source_name: Optional[str] = "Definitive"
    client: str


class client_payload(BaseModel):
    """
    Pydantic class to validate the payload for client details
    """
    user_email: str
    department: str
    client_specific: bool


class definitive_client_payload(BaseModel):
    """
    Pydantic class to validate the payload for Definitive client details
    """
    department: str
    source: Optional[str] = "Definitive"


class breakingnews_data(BaseModel):
    """
    BaseModel class for the input to be provided to the Breaking News DB endpoints
    """
    start_date: str
    end_date: str
    department: str

class source_data(BaseModel):
    """
    BaseModel class for the input to be provided to the DB endpoints
    """
    emp_id: str
    source_name: List[str]
    client: List[str]
    start_date: str
    end_date: str
    sentiment_list: conlist(str, min_length=1, max_length=3)
    pageInformation:str # =Field(default="client-news-digest") #######To be removed in future

@router.post("/fetch_client", tags=['Client/Non client Main Page'])
async def get_client_details(fetch: client_payload, token_details: dict = Depends(validate_user)):
    """
    Endpoint to fetch client details.

    Args:
        fetch (client_payload): The payload containing user email and department.

    Returns:
        JSONResponse: A JSON response with the status, message, and data.

    Raises:
        Exception: If an error occurs during data retrieval.
    """
    try:
        data = {}
        fav_client = user_db.query_fav_client(fetch.user_email)
        client_list = client_db.query_client(fetch.department)
        a = []
        for i in client_list:
            client = {'name': i, 'isFavourite': i in fav_client[0]}
            a.append(client)
        a = sorted(a, key=lambda x: x['name'])
        data['client'] = a
        data['sourceList'] = sourcedb.query_source(fetch.department, fetch.client_specific)

        return JSONResponse({'status': "success", 'message': "Data Sent Successfully", "data": data,
                             "user_details": token_details})
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading DB data Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return JSONResponse({'status': "failed", 'message': "Data Sent failed", "data": []})


@router.post("/source_data", tags=['Client/Non client Main Page'])
async def get_source_data(fetch: source_data, token_details: dict = Depends(validate_user)):
    """
        Fetches data from the database based on the given parameters.
 
        Args:
            fetch (db_data): The parameters for fetching data from the database.
            token_details (dict, optional): The user details.Default Depends(validate_user).
 
        Returns:
            JSONResponse: The fetched data along with the user details if successful, or an error message if not.
 
        Raises:
            HTTPException: If no data is found for the given parameters.
    """
    try:
        start_time = time.time()
        emp_id = fetch.emp_id
        source_name = fetch.source_name
        client = fetch.client
        start_date = fetch.start_date
        end_date = fetch.end_date
        sentiment_list = fetch.sentiment_list
        pageInformation = fetch.pageInformation
 
        data = db_ops.query_items(source_name, client, start_date, end_date, sentiment_list)
        if not data:
            raise HTTPException(status_code=404, detail="No data found for the given date")
        deduplicate_data = helper.deduplicate_dicts(data, "news_url")
 
        deduplicate_data = [dict(item, **{'isThumbsUp': False, 'isThumbsDown': False}) for item in deduplicate_data]

        try:
            feedbacks = feedback_db.query_items(emp_id,pageInformation,search_query="")

            if feedbacks:
                results = helper.add_feedback_indicator(deduplicate_data, feedbacks)
            else:
                results = deduplicate_data
        except Exception as e:
            logger.error("Feedback Mechanism Break str(e)")
            results = deduplicate_data
 
        # deduplicate_data = sorted(deduplicate_data, key=lambda x: x['news_date'], reverse=True)
        results = sorted(results, key=lambda x: x['news_date'], reverse=True)
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Data fetched successfully!  Total Time: {total_time}")
        return JSONResponse({'status': "success", 'message': "Data extracted from DB", "data": results,
                             "user_details": token_details})
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading DB data Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return JSONResponse({'status': "failed", 'message': "Data extraction failed", "data": []})


@router.post("/fetch_definitive_client", tags=['Definitive'])
async def get_definitive_client_details(fetch: definitive_client_payload,
                                        token_details: dict = Depends(validate_user)):
    """
        This function retrieves definitive client details.

        Args:
            fetch (definitive_client_payload): The payload containing department and source.

        Returns:
            dict: A dictionary with status, message, and data.

        Raises:
            Exception: If an error occurs during data retrieval.
        """
    try:
        data = {}

        # Query client details from the database
        client_list = definitiveclientdb.query_client(fetch.department, fetch.source)

        # Assign a client list to 'client' key in data dictionary
        data['client'] = client_list
        return {'status': "success", 'message': "Data Sent Successfully", "data": data}
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading DB data Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        logger.info(f"Exception {e} occurred while loading data from DB")
        return {'status': "failed", 'message': "Data Sent failed", "data": [],
                "user_details": token_details}


@router.post("/definitive_data", tags=['Definitive'])
async def get_source_data(fetch: def_data, token_details: dict = Depends(validate_user)):
    """
    Endpoint to extract stored data from DB filtered on timestamp given
    params:
        source_name: source from which news is to be extracted; in this case Becker review hospital
        client: search keyword or client name for which data is to be filtered on
    returns:
        list of dictionary containing metrics from definitive
    """
    try:
        start_time = time.time()
        source_name = fetch.source_name
        client = fetch.client

        data = db_ops.query_def_items(source_name, client)
        if not data:
            raise HTTPException(status_code=404, detail="No data found for the given date")
            return JSONResponse({'status': "failed", 'message': "No data found", "data": [],
                                 "user_details": token_details})

        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Data fetched successfully!  Total Time: {total_time}")
        return JSONResponse({'status': "success", 'message': "Data extracted from DB", "data": data,
                             "user_details": token_details})
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading DB data Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return JSONResponse({'status': "failed", 'message': "Data extraction failed", "data": []})


@router.post("/download_excel", tags=['Client/Non client Main Page'])
async def download_excel(fetch: db_data, background_tasks: BackgroundTasks,
                         token_details: dict = Depends(validate_user)):
    """
    Endpoint to download data in Excel
    params:
        start_date: from 
        end_date: to
        source_name: source/s for which data is to be extracted
        client: client/s for which data is to be extracted
    returns:
        data extracted from DB in Excel format
    """
    try:
        start_time = time.time()
        logger.info('Querying for items in database to load to excel')
        data = db_ops.query_items(fetch.source_name, fetch.client, fetch.start_date, fetch.end_date,
                                  fetch.sentiment_list)
        if not data:
            raise HTTPException(status_code=404, detail="No data found for the given date")
        deduplicate_data = helper.deduplicate_dicts(data, "news_url")
        final_data = sorted(deduplicate_data, key=lambda x: x['news_date'], reverse=True)

        df = helper.create_dataframe(final_data)

        # Drop a client for a non-client news source
        if fetch.client == [""]:
            df = df.drop(columns=['Client'])

        f_path, file_name = helper.file_path()

        helper.create_excel(df, f_path)

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
        return {'status': "failed", 'message': "Unable to download excel file", "data": {}}


@router.post("/breaking_news", tags=['Client/Non client Main Page'])
async def get_breaking_news(fetch: breakingnews_data, token_details: dict = Depends(validate_user)):
    """
    Endpoint to extract stored data from DB filtered on timestamp given
    params:
        start_date: from when breaking news to be extracted
        end_date: till when breaking news to be extracted

    returns:
        list of dictionary containing news_url, news_summary, sentiment, keywords_list, news_date
    """
    try:
        start_time = time.time()
        start_date = fetch.start_date
        end_date = fetch.end_date
        department = fetch.department
        data = db_ops.query_breaking_news(department, start_date, end_date)
        if not data:
            raise HTTPException(status_code=404, detail="No data found for the given date")
        deduplicate_data = helper.deduplicate_dicts(data, "news_url")

        deduplicate_data = sorted(deduplicate_data, key=lambda x: x['news_date'], reverse=True)
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Breaking News Data fetched successfully!  Total Time: {total_time}")
        return JSONResponse(
            {'status': "success", 'message': "Breaking News Data extracted from DB", "data": deduplicate_data,
             "user_details": token_details})
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading Breaking News data Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return JSONResponse({'status': "failed", 'message': "Breaking News Data extraction failed", "data": []})



class DefinitiveExcel(BaseModel):
    table_list: List[str]
    source: str = 'Definitive'
    client_name: str


@router.post("/download_definitive_excel", tags=['Definitive'])
async def download_definitive_excel(fetch: DefinitiveExcel, background_tasks: BackgroundTasks,
                                    token_details: dict = Depends(validate_user)):
    """
      Downloads Excel file based on the given parameters.

      Args:
          fetch (DefinitiveExcel): The parameters for the Excel file.
          background_tasks (BackgroundTasks): The background tasks.

      Returns:
          FileResponse: The Excel file.

      Raises:
          HTTPException: If no data is found.
      """
    try:
        start_time = time.time()
        data = db_ops.query_definitive_data_excel(fetch.table_list, fetch.source, fetch.client_name)
        if not data:
            raise HTTPException(status_code=404, detail="No data found for the given client and tables")
        f_path, file_name = helper.file_path(name_initial="Definitive_")
        helper.create_definitive_excel(data, f_path)
        background_tasks.add_task(helper.delete_file_after_delay, f_path)
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Excel file created: {f_path} Total Time: {total_time}")

        # Return the file as a response
        return FileResponse(path=f_path, filename=file_name,
                            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'status': "failed", 'message': "Unable to download excel file", "data": {}}


@router.post("/fetch_client_non_admin_manage", tags=['Manage Account(Member)'])
async def get_client_details_non_admin_manage(fetch: client_payload, token_details: dict = Depends(validate_user)):
    """
    Endpoint to fetch the table details for a normal user in the manage account page.

    Args:
        fetch (client_payload): The payload containing user email and department.

    Returns:
        JSONResponse: A JSON response with the status, message, and data.

    Raises:
        Exception: If an error occurs during data retrieval.
    """
    try:
        fav_client,email_notify = user_db.query_fav_client_and_email_status(fetch.user_email)
        client_list = client_db.query_client_synonyms(fetch.department)
        for i in range(0, len(client_list)):
            client_list[i]['isFavourite'] = False
            if client_list[i]['synonyms'].strip() == "":
                client_list[i]['synonyms'] = "-"
            if client_list[i]['client_name'] in fav_client[0]:
                client_list[i]['isFavourite'] = True

        sorted_client_list = sorted(client_list, key=lambda x: x['client_name'])
        data = {"user_client_list": sorted_client_list, "email_notify": email_notify}

        return {'status': "success", 'message': "Data Sent Successfully", "data": data,
                "user_details": token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading DB data Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'status': "failed", 'message': "Data Sent failed", "data": []}


class admin_client_payload(BaseModel):
    """
    Pydantic class to validate the payload for client details
    """
    user_email: EmailStr
    department: str


class admin_keyword_payload(BaseModel):
    """
    Pydantic class to validate the payload for keywords details
    """
    user_email: EmailStr
    department: str


@router.post("/fetch_admin_client", tags=['Manage Account(Admin)'])
async def get_client_details(fetch: admin_client_payload, token_details: dict = Depends(validate_user)):
    """
    Endpoint to get the admin table details for manage accounts table.

    Args:
        fetch (admin_client_payload): The payload containing user email and department.

    Returns:
        dict: A dictionary with the status, message, and data.

    Raises:
        Exception: If an error occurs during data retrieval.
    """
    try:
        if token_details['role'] not in ['Admin']:
            raise HTTPException(status_code=401, detail="Unauthorised Access for the User")
        # Query the admin table details for the specified department
        client_list = client_db.query_admin_table(department_name=fetch.department)

        # Update client data with default values if the key is not present
        for client in client_list:
            #client['synonyms'] = client.get('synonyms', '-')
            if len(client['synonyms'].strip()) == 0:
                client['synonyms'] = "-"
        sorted_client_list = sorted(client_list, key=lambda x: x['client_name'])
        return {'status': "success", 'message': "Data Sent Successfully", "data": sorted_client_list,
                "user_details": token_details}
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading DB data Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'status': "failed", 'message': "Data Sent failed", "data": []}


@router.post("/fetch_admin_keywords", tags=['Manage Account(Admin)'])
async def get_keywords_details(fetch: admin_keyword_payload, token_details: dict = Depends(validate_user)):
    """
    Endpoint to get the admin table details for manage accounts table.

    Args:
        fetch (admin_keyword_payload): The payload containing user email and department.

    Returns:
        dict: A dictionary with the status, message, and data.

    Raises:
        Exception: If an error occurs during data retrieval.
    """
    try:
        if token_details['role'] not in ['Admin']:
            raise HTTPException(status_code=401, detail="Unauthorised Access for the User")

        # Query the keyword table details for the specified department
        keyword_list = keyword_db.query_admin_table(department_name=fetch.department)

        sorted_keyword_list = sorted(keyword_list, key=lambda x: x['keyword_name'])
        return {'status': "success", 'message': "Data Sent Successfully", "data": sorted_keyword_list,
                "user_details": token_details}
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in loading DB data Line No: "
                     f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'status': "failed", 'message': "Data Sent failed", "data": []}
