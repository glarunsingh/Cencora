import hashlib
import logging
import os
import sys
import time

from azure.cosmos import CosmosClient as cs
from dotenv import load_dotenv

from utils.logs import create_log

_ = load_dotenv(r'.\config\db.env')

logger = create_log(name="HIMSS", level=logging.INFO)


class DBOPS:

    def __init__(self):
        try:
            self.URL = os.environ['COSMOS_ENDPOINT']
            self.KEY = os.environ['COSMOS_KEY']
            self.DATABASE_NAME = os.environ['COSMOS_NEWS_DATABASE']
            self.NEWS_CONTAINER_NAME = os.environ['COSMOS_NEWS_CONTAINER']
            self.KEY_CONTAINER_NAME = os.environ['COSMOS_KEY_CONTAINER']
            self.CLIENT_INF_CONTAINER_NAME = os.environ['COSMOS_CLIENT_INF_CONTAINER']
            self.USER_DATA_CONTAINER = os.environ['COSMOS_USER_DATA_CONTAINER']
            self.read_client = cs(self.URL, credential=self.KEY)
            self.database = self.read_client.get_database_client(self.DATABASE_NAME)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    @staticmethod
    def sha_conversion(data: str) -> str:
        sha256 = hashlib.sha256(data.encode('utf-8')).hexdigest()
        return sha256

    def query_items(self, query, container_name, cross_partition=True):
        try:
            container = self.database.get_container_client(container_name)
            results = list(container.query_items(query=query,
                                                 enable_cross_partition_query=cross_partition))
            return results

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def upsert_items(self, data, container_name):
        try:
            container = self.database.get_container_client(container_name)
            container.upsert_item(data)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def get_department_name(self):
        try:
            query = "SELECT DISTINCT(c.department_name) FROM c"
            results = self.query_items(query, self.CLIENT_INF_CONTAINER_NAME)
            final_result = [item['department_name'] for item in results]
            return final_result

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def get_clients_name(self, department_name):
        try:
            query = f"SELECT c.client_name FROM c WHERE c.department_name='{department_name}'"
            results = self.query_items(query, self.CLIENT_INF_CONTAINER_NAME, cross_partition=False)
            final_result = [item['client_name'] for item in results]
            return final_result

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def update_client_data(self, details):
        try:
            item = {
                'id': self.sha_conversion(details.email_id),
                'emp_id': details.emp_id,
                'first_name': details.first_name,
                'last_name': details.last_name,
                'email_id': details.email_id,
                'favorite_client_list': details.favourite_client_list,
                'email_notify': details.email_notify,
                'department_name': details.department_name
            }
            self.upsert_items(item, self.USER_DATA_CONTAINER)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception
