import asyncio
import logging
import os
import sys
import time

from azure.cosmos.aio import CosmosClient
from dotenv import load_dotenv

from azure.cosmos import CosmosClient as cs
from utils.logs import create_log
from utils.url_parameters import sha_conversion

_ = load_dotenv(r'.\config\db.env')

logger = create_log(name="HIMSS", level=logging.INFO)


class HIMSSDBOPS:

    def __init__(self):
        self.URL = os.environ['COSMOS_ENDPOINT']
        self.KEY = os.environ['COSMOS_KEY']
        self.DATABASE_NAME = os.environ['COSMOS_NEWS_DATABASE_DC']
        self.NEWS_CONTAINER_NAME = os.environ['COSMOS_NEWS_CONTAINER_DC']
        self.KEY_CONTAINER_NAME = os.environ['COSMOS_KEY_CONTAINER_DC']
        self.read_client = cs(self.URL, credential=self.KEY)
        self.database = self.read_client.get_database_client(self.DATABASE_NAME)

    async def upsert_data(self, data):
        try:
            async with CosmosClient(self.URL, credential=self.KEY) as client:
                database = client.get_database_client(self.DATABASE_NAME)
                container = database.get_container_client(self.NEWS_CONTAINER_NAME)
                for item in data:
                    # sha generation of url
                    print("item:\t\t", item['news_url'], "\n\n")
                    item['id'] = sha_conversion(item['news_url'])

                    await container.upsert_item(item)
            print(item)
            logger.info(f"Items uploaded! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error Uploading data - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def query_items(self, input_date: list, excel=False):
        try:
            container = self.database.get_container_client(self.NEWS_CONTAINER_NAME)
            logger.info('Querying for items in database')

            query_join = " OR ".join([f"STARTSWITH(c.news_date,'{date}')" for date in input_date])
            if excel:
                queryText = ("SELECT c.news_date,c.news_title,c.news_summary,c.sentiment,c.news_url FROM c WHERE "
                             "c.source_name = 'Drug Channel' AND (") + query_join + ")"
            else:
                # queryText = (
                #     f"SELECT c.news_url,c.news_title,c.news_date,c.news_summary,c.sentiment,c.keywords_list FROM c WHERE ("
                #     f"STARTSWITH(c.news_date,'{input_date}') AND c.source_name = 'Drug Channel')")
                queryText = (
                                "SELECT c.news_url,c.news_title,c.news_date,c.news_summary,c.sentiment,c.keywords_list "
                                "FROM c WHERE c.source_name = 'Drug Channel' AND (") + query_join + ")"
            print(queryText)
            item_list = list(container.query_items(query=queryText))
            print(item_list)
            logger.info(f"Items queried! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
            return item_list

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying data - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def query_urls(self, month, year):
        try:
            input_date = f"{year:04}-{month:02}"
            logger.info('Querying urls in database ')
            container = self.database.get_container_client(self.NEWS_CONTAINER_NAME)
            print("start_date:\t", input_date, type(input_date))
            queryText = (f"SELECT  c.source_name,c.client_name,c.news_url,c.news_title,c.news_date,c.news_content,"
                         f"c.news_summary,c.keywords_list,c.sentiment FROM c WHERE STARTSWITH(c.news_date,'{input_date}')"
                         f"AND c.source_name = 'Drug Channel'")
            print(queryText)
            item_list = list(container.query_items(query=queryText))
            url_list = [item['news_url'] for item in item_list]
            logger.info(f"Urls queried! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
            print(item_list, url_list)
            return item_list, url_list
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying urls - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

    def query_keyword_list(self, department_name):
        try:
            logger.info('Querying keywords in database')
            container = self.database.get_container_client(self.KEY_CONTAINER_NAME)
            queryText = f"SELECT c.keyword_name FROM c WHERE c.department_name = '{department_name}'"
            print(queryText)
            item_list = list(container.query_items(query=queryText))
            key_list = [item['keyword_name'] for item in item_list]
            logger.info(f"Keywords queried! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
            return key_list

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying keywords - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []
