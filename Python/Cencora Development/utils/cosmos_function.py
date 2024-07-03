import asyncio
import hashlib
import json
import logging
import os
import sys

from azure.cosmos.aio import CosmosClient
from dotenv import load_dotenv

from utils.logs import create_log

_ = load_dotenv(r'.\config\db.env')

URL = os.environ['COSMOS_ENDPOINT']
KEY = os.environ['COSMOS_KEY']
DATABASE_NAME = os.environ['COSMOS_DATABASE_DC']
CONTAINER_NAME = os.environ['COSMOS_CONTAINER_DC']

logger = create_log(name="Drug_Channel", level=logging.INFO)


def sha_conversion(url: str) -> str:
    sha256 = hashlib.sha256(url.encode('utf-8')).hexdigest()
    return sha256


async def upsert_data(data):
    try:
        async with CosmosClient(URL, credential=KEY) as client:
            database = client.get_database_client(DATABASE_NAME)
            container = database.get_container_client(CONTAINER_NAME)
            for item in data:
                # sha generation of url
                print("item:\t\t", item['news_url'], "\n\n")
                item['id'] = sha_conversion(item['news_url'])

                await container.upsert_item(item)
        print(item)
        logger.info(f"Items uploaded! Container: {CONTAINER_NAME}\tDatabase: {DATABASE_NAME} ")
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error Uploading data - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        raise Exception


async def query_items(input_date):
        try:
            logger.info('Querying for items in database')

            async with CosmosClient(URL, credential=KEY) as client:
                database = client.get_database_client(DATABASE_NAME)
                container = database.get_container_client(CONTAINER_NAME)
                print("start_date:\t", input_date,type(input_date))
                queryText = (f"SELECT c.news_url,c.news_title,c.news_date,c.news_summary FROM c WHERE (STARTSWITH("
                             f"c.news_date,'{input_date}') AND c.source_name = 'Drug Channel')")
                print(queryText)
                results = container.query_items(query=queryText)

                item_list = [item async for item in results]

            for item in item_list:
                print("item:",item)
            #item_list.append(item)

            logger.info(f"Items queried! Container: {CONTAINER_NAME}\tDatabase: {DATABASE_NAME} ")
            print(item_list)
            return item_list

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying data - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception


async def query_urls(month,year):
    try:
        input_date=f"{year:04}-{month:02}"
        logger.info('Querying urls in database ')

        async with CosmosClient(URL, credential=KEY) as client:
            database = client.get_database_client(DATABASE_NAME)
            container = database.get_container_client(CONTAINER_NAME)
            print("start_date:\t", input_date, type(input_date))
            queryText = (f"SELECT  c.source_name,c.client_name,c.news_url,c.news_title,c.news_date,c.news_content,"
                         f"c.news_summary,c.keywords_list,c.sentiment FROM c WHERE STARTSWITH(c.news_date,'{input_date}') "
                         f"AND c.source_name = 'Drug Channel'")
            print(queryText)
            results = container.query_items(query=queryText)

            item_list = [item async for item in results]

        url_list = [item['news_url'] for item in item_list]
        logger.info(f"Urls queried! Container: {CONTAINER_NAME}\tDatabase: {DATABASE_NAME} ")

        return item_list,url_list

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error querying urls - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return []




