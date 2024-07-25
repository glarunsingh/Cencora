from azure.cosmos import CosmosClient
from azure.cosmos import  exceptions, PartitionKey
import os
import hashlib
from dotenv import load_dotenv
import sys

_= load_dotenv("./BingNews/config/config.env")

import logging
from BingNews.utils.logger import create_log
logger = create_log(name="bing_news", level=logging.INFO)

COSMO_URL = os.environ['COSMOS_ENDPOINT']
COSMO_KEY = os.environ['COSMOS_KEY']
DATABASE_NAME = os.environ['COSMOS_NEWS_DATABASE']
NEWS_CONTAINER_NAME = os.environ['COSMOS_NEWS_CONTAINER']
CLIENT_CONTAINER_NAME = os.environ['COSMOS_CLIENT_CONTAINER']
KEYWORD_CONTAINER_NAME= os.environ['COSMOS_KEY_CONTAINER']

def sha_conversion(url: str) -> str:
    sha256 = hashlib.sha256(url.encode('utf-8')).hexdigest()
    return sha256

class Bing_News_DB:

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
            
    def query_items(self,source_name,client_name,start_date,end_date):
        try:
            container = self.database.get_container_client(self.NEWS_CONTAINER_NAME)
            logger.info('Querying for items in database')
            client_name = str(client_name)
            client_name = client_name.replace("[","(")
            client_name = client_name.replace("]",")")
            #query_text = f"SELECT c.news_url,c.news_date,c.news_summary,c.sentiment,c.keywords_list\
            #    FROM c WHERE c.source_name='{source_name}' and c.client_name in {client_name} and \
            #        c.news_date >='{start_date}' and c.news_date<= '{end_date}'"
            #print(query_text)
            #items = list(container.query_items(query=query_text,enable_cross_partition_query=True))
            
            items = list(container.query_items(
                query="SELECT c.news_url,c.news_date,c.news_summary,c.sentiment,c.keywords_list\
                FROM c WHERE c.source_name=@source_name and c.client_name in @client_name and \
                    c.news_date >=@start_date and c.news_date<= @end_date",
                parameters=[
                    { "name":"@source_name", "value": source_name },
                    {"name":"@client_name","value":client_name},
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
            # query_text = f"SELECT c.source_name,c.client_name,c.news_title,c.news_date,c.news_url,c.description,c.news_content,c.news_summary,c.keywords_list,c.sentiment,c.breaking_news\
            #    FROM c WHERE c.source_name='{source_name}'and c.news_url IN {tuple(url_list)}"
            #print(query_text)
            #items = list(container.query_items(query=query_text,enable_cross_partition_query=True))
            
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
        
    def query_urls(self,client_name, source_name="Bing News"):
        try:
            logger.info(f"Extracting url list for client {client_name}")
            container = self.database.get_container_client(self.NEWS_CONTAINER_NAME)
            #query_text = f"SELECT c.news_url FROM c WHERE c.source_name='{source_name}' and c.client_name='{client_name}'"
            #print(query_text)
            #items = list(container.query_items(query= query_text))
            items = list(container.query_items(
                query="SELECT r.news_url FROM r WHERE r.source_name=@source_name and r.client_name = @client_name",
                parameters=[
                    { "name":"@source_name", "value": source_name },
                    {"name":"@client_name","value":client_name}
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
            #queryText = f"SELECT c.keyword_name FROM c WHERE c.department_name = '{department_name}'"
            #print(queryText)
            #item_list = list(container.query_items(query=queryText))
            
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
        
    def query_client_list(self, department_name):
        try:
            logger.info('Querying Client in database')
            print('Querying Client in database')
            container = self.database.get_container_client(self.CLIENT_CONTAINER_NAME)
            #queryText = f"SELECT c.client_name,c.synonyms FROM c WHERE c.department_name = '{department_name}'"
            #print(queryText)
            #item_list = list(container.query_items(query=queryText))
            
            item_list = list(container.query_items(
                query="SELECT r.client_name,r.synonyms FROM r WHERE r.department_name=@department_name",
                parameters=[
                    {"name":"@department_name","value":department_name}
                ],
                enable_cross_partition_query=True
            ))
            
            client_list=[]
            for item in item_list:
                input_string = f"{item['client_name'].strip()}"
                parts= [f'"{input_string}"']
                if item['synonyms']!="":
                    parts.extend([f'"{part.strip()}"' for part in item['synonyms'].split(',')])

                # Join the parts with " | "
                item['search_term'] = " | ".join(parts)
                client_list.append(item)
            
            logger.info(f"Clients queried! Container: {self.CLIENT_CONTAINER_NAME}\tDatabase: {self.DATABASE_NAME} ")
            return client_list

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error querying Client list - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []
    
    def clean_data(self,source_name):
    
        container = self.database.get_container_client(self.KEYWORD_CONTAINER_NAME)
        query_text = f"SELECT * FROM c WHERE c.source_name='{source_name}'" 
        documents_to_delete = list(container.query_items(query=query_text))
        # Delete each document
        for doc in documents_to_delete:
            print(doc['source_name'])
            container.delete_item(item=doc,partition_key= doc['source_name'])