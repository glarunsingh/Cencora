"""
File to create Database operation for Azure AI search
"""
from datetime import datetime

from dotenv import load_dotenv

_ = load_dotenv('db.env')

import sys
import logging
from azure.cosmos import CosmosClient as cs
import os

logger = logging.getLogger(__name__)


class DBOPS:
    """
    Class to perform Database operations.
    """

    def __init__(self):
        """
        Initialising DBOPS for Azure AI services
        """
        try:
            logger.info("Initialising DBOPS for Azure AI services")
            self.URL = os.environ['COSMOS_ENDPOINT']
            self.KEY = os.environ['COSMOS_KEY']
            self.DATABASE_NAME = os.environ['COSMOS_NEWS_DATABASE']
            self.NEWS_CONTAINER_NAME = os.environ['COSMOS_NEWS_CONTAINER']
            self.CONFIG_CONTAINER_NAME = os.environ['COSMOS_CONFIG_CONTAINER']
            self.read_client = cs(self.URL, credential=self.KEY)
            self.database = self.read_client.get_database_client(self.DATABASE_NAME)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Failed to Connect to Database - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)
            raise Exception

    def query_items(self, query, container_name, cross_partition=True):
        """
        query the items from the database
        """
        try:
            logger.info(f"Querying data from Container:{container_name}")
            container = self.database.get_container_client(container_name)
            results = list(container.query_items(query=query,
                                                 enable_cross_partition_query=cross_partition))
            return results
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(
                f"Failed to Query data from Container:{container_name} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                stack_info=True)
            raise Exception

    def upsert_items(self, data, container_name):
        """
        update/insert the items in the database
        """
        try:
            logger.info(f"Uploading data to Container:{container_name}")
            container = self.database.get_container_client(container_name)
            container.upsert_item(data)
            logger.info(f"Data uploaded to Container:{container_name}")

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Failed to Upsert data - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def get_last_updated_timestamp(self):
        """
        get the last updated details of Azure AI Search from the database
        """
        try:
            logger.info("Getting the last updated details to Azure AI Search")
            queryText = "SELECT c.last_timestamp FROM c WHERE c.property = 'last_updated_details'"
            results = self.query_items(query=queryText, container_name=self.CONFIG_CONTAINER_NAME)
            return results[0]['last_timestamp']

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(
                f"Unable to get the last updated details from DB - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                stack_info=True)
            raise Exception

    def get_items(self, last_updated_timestamp):
        """
        Get the items from the database to be indexed in Azure AI Search
        """
        try:
            logger.info("Getting the items to be indexed in Azure AI Search")
            logger.info(f"The last indexed article was on: {str(datetime.fromtimestamp(last_updated_timestamp))}\nIndexing article after that time")
            queryText = (f"SELECT c.id,c.source_name,c.client_name,c.news_url,c.news_title,c.news_date,c.news_content,"
                         f"c.news_summary,c.sentiment,c._ts FROM c WHERE IS_DEFINED(c.news_content) AND "
                         f"c._ts > {last_updated_timestamp} ORDER BY c._ts ASC")
            results = self.query_items(query=queryText, container_name=self.NEWS_CONTAINER_NAME)
            logger.info(f"{len(results)} articles found to be indexed")
            return results
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Unable to get the item details - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)
            raise Exception

    def save_new_timestamp(self, new_timestamp, current_utc_time,last_updated_by):
        """
        Method to save the timestamp of latest news indexed in Azure AI search.
        Args:
            current_utc_time:timestamp when the last time indexing was done.
            new_timestamp: timestamp of last news indexed in Azure AI search
        """
        logger.info("Saving the timestamp of the last news indexed in Azure AI search")
        try:
            queryText = ("SELECT c.source_name,c.property,c.last_timestamp,c.last_updated_by,c.id,"
                         "c.indexer_last_ran_time FROM c WHERE c.property = 'last_updated_details'")
            config_details = self.query_items(query=queryText, container_name=self.CONFIG_CONTAINER_NAME)[0]
            print("adasD",new_timestamp)
            logger.info(f"Saving {new_timestamp} as the last news indexed timestamp and source as '{last_updated_by}' "
                        f"in the DB")
            config_details['last_timestamp'] = new_timestamp
            config_details['indexer_last_ran_time'] = current_utc_time
            config_details['last_updated_by'] = last_updated_by
            self.upsert_items(config_details, self.CONFIG_CONTAINER_NAME)
            logger.info("Last news indexed timestamp saved successfully")

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Failed to save the last news indexed timestamp in the DB - Line No: {exc_tb.tb_lineno} "
                         f"Error: {str(e)}",stack_info=True)
            raise Exception
