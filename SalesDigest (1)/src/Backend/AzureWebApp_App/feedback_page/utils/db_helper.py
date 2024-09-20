"""
Module for DB operations
"""
from azure.cosmos import CosmosClient as cs
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import os
import sys
import hashlib
#from dotenv import load_dotenv
#load_dotenv()
from config.key_vault import key_vault
secret_value = key_vault()

import logging
logger = logging.getLogger(__name__)

class DBOPS:
    """
    Main class for DBOPs
    """

    def __init__(self):
        self.URL = secret_value.get_secret('COSMOS-ENDPOINT')
        self.KEY = secret_value.get_secret('COSMOS-KEY')
        #self.URL = os.getenv('COSMOS-ENDPOINT')
        #self.KEY = os.getenv('COSMOS-KEY')
        self.DATABASE_NAME = os.environ['COSMOS_NEWS_DATABASE']
        # self.NEWS_CONTAINER_NAME = os.environ['COSMOS_NEWS_CONTAINER']
        # self.KEY_CONTAINER_NAME = os.environ['COSMOS_KEY_CONTAINER']
        # self.CLIENT_INF_CONTAINER_NAME = os.environ['COSMOS_CLIENT_CONTAINER']
        # self.USER_DATA_CONTAINER = os.environ['COSMOS_USER_CONTAINER']
        self.container_name = os.environ['COSMOS_USER_FEEDBACK_CONTAINER'] ## new add
        # self.partition_key = os.environ['PARTITION_KEY']
        self.read_client = cs(self.URL, credential=self.KEY)
        self.database = self.read_client.get_database_client(self.DATABASE_NAME)

    def upsert_items(self, data):
        try:
            container = self.database.get_container_client(self.container_name)
            container.upsert_item(data)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def delete_items(self, data, partition_key):
            delete_flag = False
            try:
                container = self.database.get_container_client(self.container_name)
                container.delete_item(item=data, partition_key=partition_key)
                delete_flag = True
            except exceptions.CosmosResourceNotFoundError:
                logger.info(f"User {data} does not exist")
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
                raise Exception
            return delete_flag
    
    def query_items(self, emp_id, page_information,search_query=""):
        try:
            # make search query case-insensitive and strip leading and trailing spaces
            search_query = search_query.strip().lower()
            container = self.database.get_container_client(self.container_name)
            feedbacks = list(container.query_items(
                query="SELECT  c.news_url, c.feedback, c.pageInformation FROM c where c.emp_id=@emp_id and "
                      "c.pageInformation=@pageInformation and lower(c.search_query)=@search_query",
                parameters=[
                {"name": "@emp_id", "value": emp_id},
                {"name": "@pageInformation", "value": page_information},
                {"name": "@search_query", "value": search_query}
            ],
            enable_cross_partition_query=True
            ))
            return feedbacks
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception