from azure.cosmos import CosmosClient
import os
import hashlib
import sys

import logging
logger = logging.getLogger(__name__)

COSMO_URL =  os.environ['COSMOS_ENDPOINT'] #secret_value.get_secret('COSMOS-ENDPOINT')
COSMO_KEY = os.environ['COSMOS_KEY'] #secret_value.get_secret('COSMOS-KEY')
DATABASE_NAME = os.environ['COSMOS_NEWS_DATABASE']
NEWS_CONTAINER_NAME = os.environ['COSMOS_NEWS_CONTAINER']
CLIENT_CONTAINER_NAME = os.environ['COSMOS_CLIENT_CONTAINER']
KEYWORD_CONTAINER_NAME= os.environ['COSMOS_KEY_CONTAINER']

def sha_conversion(url: str) -> str:
    sha256 = hashlib.sha256(url.encode('utf-8')).hexdigest()
    return sha256

class News_DB:

    def __init__(self):
        self.URL = COSMO_URL
        self.KEY = COSMO_KEY
        self.DATABASE_NAME = DATABASE_NAME
        self.NEWS_CONTAINER_NAME = NEWS_CONTAINER_NAME
        self.KEYWORD_CONTAINER_NAME = KEYWORD_CONTAINER_NAME
        self.CLIENT_CONTAINER_NAME = CLIENT_CONTAINER_NAME
        self.cosmo_client = CosmosClient(self.URL, credential=self.KEY)
        self.database = self.cosmo_client.get_database_client(self.DATABASE_NAME)
        
    def upsert_data(self, data):
        try:
            container = self.database.get_container_client(self.NEWS_CONTAINER_NAME)
            for item in data:
                # sha generation of url
                item['id'] = sha_conversion(item['news_url'])
                container.upsert_item(item)
            logger.info(f"Items uploaded! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error Uploading data - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception
            
    def query_items(self,source_name,start_date,end_date):
        try:
            container = self.database.get_container_client(self.NEWS_CONTAINER_NAME)
            logger.info('Querying for items in database')


            items = list(container.query_items(
                query="SELECT c.news_url,c.news_date,c.news_summary,c.sentiment\
                FROM c WHERE c.source_name=@source_name and \
                    c.news_date >=@start_date and c.news_date<= @end_date",
                parameters=[
                    { "name":"@source_name", "value": source_name },
                    { "name":"@start_date", "value": start_date },
                    { "name":"@end_date", "value": end_date }
                ],
                enable_cross_partition_query=True
            ))
            
            items = sorted(items, key=lambda x: x['news_date'], reverse=True)
            #item_list = list(container.query_items(query=queryText))
            print(items)
            logger.info(f"Items queried! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
            return items

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying data - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception
    
    def query_url_data(self,source_name,url_list):
        try:
            container = self.database.get_container_client(self.NEWS_CONTAINER_NAME)
            url_list = str(url_list)
            url_list = url_list.replace("[","(")
            url_list = url_list.replace("]",")")
            logger.info('Querying for items in database')

            items = list(container.query_items(
                query="SELECT r.source_name,r.client_name,r.news_title,r.news_date,r.news_url,r.description,r.news_content,r.news_summary,r.keywords_list,r.sentiment,r.breaking_news\
                    FROM r WHERE r.source_name=@source_name and r.news_url IN @url_list",
                parameters=[
                    { "name":"@source_name", "value": source_name },
                    {"name":"@url_list","value":url_list}
                ],
                enable_cross_partition_query=True
            ))
            
            
            logger.info(f"Items queried! Container: {self.NEWS_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
            return items

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying data - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception
        
    def query_urls(self,source_name):
        try:
            logger.info(f"Extracting url list for source {source_name}")
            container = self.database.get_container_client(self.NEWS_CONTAINER_NAME)
            items = list(container.query_items(
                query="SELECT r.news_url FROM r WHERE r.source_name=@source_name",
                parameters=[
                    { "name":"@source_name", "value": source_name }
                ],
                enable_cross_partition_query=True
            ))
            
            url_list = [i['news_url'] for i in items]
            return url_list
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying urls - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []
        
    def query_keyword_list(self, department_name):
        try:
            logger.info('Querying keywords in database')
            container = self.database.get_container_client(self.KEYWORD_CONTAINER_NAME)

            item_list = list(container.query_items(
                query="SELECT r.keyword_name FROM r WHERE r.department_name=@department_name",
                parameters=[
                    {"name":"@department_name","value":department_name}
                ],
                enable_cross_partition_query=True
            ))
            key_list = [item['keyword_name'] for item in item_list]
            logger.info(f"Keywords queried! Container: {self.KEYWORD_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
            return key_list

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying keywords - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

