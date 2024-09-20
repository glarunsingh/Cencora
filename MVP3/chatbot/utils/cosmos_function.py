import asyncio
import logging
import os
import sys
import time

from azure.cosmos.aio import CosmosClient
from dotenv import load_dotenv

from azure.cosmos import CosmosClient as cs
from utils.logs import create_log
#from utils.url_parameters import sha_conversion

_ = load_dotenv(r'.\config\db.env')

logger = create_log(name="chatbot", level=logging.INFO)


class chatbotdb:
    """
    Class to perform Database operations.
    """
    def __init__(self):
        try:
            self.URL = os.environ['COSMOS_ENDPOINT']
            self.KEY = os.environ['COSMOS_KEY']
            self.DATABASE_NAME = os.environ['COSMOS_NEWS_DATABASE']
            self.NEWS_CONTAINER_NAME = os.environ['COSMOS_NEWS_CONTAINER']
            self.KEY_CONTAINER_NAME = os.environ['COSMOS_KEY_CONTAINER']
            self.read_client = cs(self.URL, credential=self.KEY)
            self.database = self.read_client.get_database_client(self.DATABASE_NAME)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Unable to Connnect to Database - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def get_latest_news_content(self):
        """
        A function to query the latest news content from the database sorted by news_date.

        Parameters:
        - self: The instance of the class.

        Returns:
        - str: The news content of the latest document.

        Raises:
        - Exception: If an error occurs during the querying process.
        """
        try:
            container = self.database.get_container_client(self.NEWS_CONTAINER_NAME)
            logger.info('Querying for the latest news content in the database')

            query_text = (
                "SELECT c.news_content "
                "FROM c "
                "ORDER BY c.news_date DESC "
                "OFFSET 0 LIMIT 1"
            )
            item_list = list(container.query_items(query=query_text, enable_cross_partition_query=True))

            if item_list:
                latest_news_content = item_list[0].get('news_content', '')
                logger.info(f"Latest news content queried! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME}")
                return latest_news_content
            else:
                logger.info("No news content found in the database.")
                return ""
        except Exception as e:
            logger.error(f"Error querying the latest news content: {str(e)}")
            raise Exception
