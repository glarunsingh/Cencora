import logging
import os
import sys

from azure.cosmos.aio import CosmosClient
from azure.cosmos import CosmosClient as cs
from DrugChannel.utils.url_parameters import sha_conversion
logger = logging.getLogger(__name__)
class DrugChannelDBOPS:
    """
    Class to perform Database operations.
    """

    def __init__(self):
        try:
            self.URL = os.environ['COSMOS_ENDPOINT']   #secret_value.get_secret('COSMOS-ENDPOINT')
            self.KEY = os.environ['COSMOS_KEY']  #secret_value.get_secret('COSMOS-KEY')
            self.DATABASE_NAME = os.environ['COSMOS_NEWS_DATABASE']
            self.NEWS_CONTAINER_NAME = os.environ['COSMOS_NEWS_CONTAINER']
            self.KEY_CONTAINER_NAME = os.environ['COSMOS_KEY_CONTAINER']
            self.read_client = cs(self.URL, credential=self.KEY)
            self.database = self.read_client.get_database_client(self.DATABASE_NAME)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Unable to Connnect to Database - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)
            raise Exception

    async def upsert_data(self, data):
        """
        Asynchronously upserts data into the CosmosDB.

        Parameters:
        - self: The instance of the class.
        - data: The data to be upserted into the database.

        Returns:
        - None

        Raises:
        - Exception: If an error occurs during the upsert process.
        """
        try:
            async with CosmosClient(self.URL, credential=self.KEY) as client:
                database = client.get_database_client(self.DATABASE_NAME)
                container = database.get_container_client(self.NEWS_CONTAINER_NAME)
                for item in data:
                    # sha generation of url
                    # print("item:\t\t", item['news_url'], "\n\n")
                    item['id'] = sha_conversion(item['news_url'])

                    await container.upsert_item(item)
            # print(item)
            logger.info(f"Items uploaded! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error Uploading data - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def query_items(self, input_date: list):
        """
        A function to query items from the database based on input dates.

        Parameters:
        - self: The instance of the class.
        - input_date (list): A list of input dates to query items.

        Returns:
        - list: A list of items queried from the database.

        Raises:
        - Exception: If an error occurs during the querying process.
        """
        try:
            container = self.database.get_container_client(self.NEWS_CONTAINER_NAME)
            logger.info('Querying for items in database')

            query_join = " OR ".join([f"STARTSWITH(c.news_date,'{date}')" for date in input_date])
            queryText = ("SELECT c.news_url,c.news_title,c.news_date,c.news_summary,c.sentiment,c.keywords_list FROM "
                         "c WHERE c.source_name = 'Drug Channel' AND (") + query_join + ")"
            item_list = list(container.query_items(query=queryText))
            logger.info(f"Items queried! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
            return item_list

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying data - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def query_urls(self, month, year):
        """
        A function to query URLs from the database based on the given month and year.

        Parameters:
        - self: The instance of the class.
        - month (int): The month for the query.
        - year (int): The year for the query.

        Returns:
        - tuple: A tuple containing two lists, item_list and url_list, where item_list holds the queried items
                 and url_list contains the URLs extracted from the items.

        Raises:
        - Exception: If an error occurs during the querying process.
        """
        try:
            input_date = f"{year:04}-{month:02}"
            logger.info('Querying urls in database ')
            container = self.database.get_container_client(self.NEWS_CONTAINER_NAME)
            # print("start_date:\t", input_date, type(input_date))
            queryText = (f"SELECT  c.source_name,c.client_name,c.news_url,c.news_title,c.news_date,c.news_content,"
                         f"c.news_summary,c.keywords_list,c.sentiment FROM c WHERE STARTSWITH(c.news_date,'{input_date}')"
                         f"AND c.source_name = 'Drug Channel'")
            # print(queryText)
            item_list = list(container.query_items(query=queryText))
            url_list = [item['news_url'] for item in item_list]
            logger.info(f"Urls queried! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
            # print(item_list, url_list)
            return item_list, url_list
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying urls - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

    def query_keyword_list(self, department_name):
        """
        Query keywords in the database based on the department name.

        Parameters:
        - department_name (str): The name of the department to filter the keywords. If None, all keywords
        will be returned.

        Returns:
        - list: A list of keywords matching the department name. If an error occurs during the querying
        process, an empty list is returned.
        """
        try:
            logger.info('Querying keywords in database')
            container = self.database.get_container_client(self.KEY_CONTAINER_NAME)
            if department_name:
                department_name = department_name.replace("'", "\\'")
                queryText = f"SELECT c.keyword_name FROM c WHERE c.department_name = '{department_name}'"
            else:
                queryText = f"SELECT c.keyword_name FROM c"
            # print(queryText)
            item_list = list(container.query_items(query=queryText, enable_cross_partition_query=True))
            key_list = [item['keyword_name'] for item in item_list]
            logger.info(f"Keywords queried! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
            return key_list

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying keywords - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []
