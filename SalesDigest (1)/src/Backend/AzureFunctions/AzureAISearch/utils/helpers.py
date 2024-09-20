"""
File to create helpers for Azure AI Search
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
import time

import aiohttp
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from langchain_text_splitters import RecursiveCharacterTextSplitter

from AzureAISearch.utils.db_operation import DBOPS
from config.load_model import embeddings
logger = logging.getLogger(__name__)

dbops = DBOPS()


class AI_Search:
    """
    Class to perform Azure AI Search operations
    """
    def __init__(self):
        """
        Initialising Azure services
        """
        try:
            logger.info("Initialising Azure AI Search services")
            self.search_service_endpoint = os.environ["AZURE_AI_SEARCH_ENDPOINT"]
            self.search_service_key = os.environ["AZURE_AI_SEARCH_API_KEY"]
            self.search_index_name = os.environ["AZURE_AI_SEARCH_INDEX_NAME"]
            self.search_client = SearchClient(endpoint=self.search_service_endpoint, index_name=self.search_index_name,
                                              credential=AzureKeyCredential(self.search_service_key))
            self.chunk_size = int(os.environ['AZURE_AI_SEARCH_CHUNK_SIZE'])
            self.chunk_overlap = int(os.environ['AZURE_AI_SEARCH_CHUNK_OVERLAP_SIZE'])
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error initialising Azure services - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)
            raise Exception

    def create_text_chunks_list(self, text, url=None):
        """
            Creates a list of text chunks from the input text.
            This method uses the RecursiveCharacterTextSplitter to split the input text into chunks
            based on the specified chunk size and overlap.
            Args:
            text:text to create text chunks
        """
        try:
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(encoding_name="cl100k_base",
                                                                                 chunk_size=self.chunk_size,
                                                                                 chunk_overlap=self.chunk_overlap)
            text_chunks = text_splitter.split_text(text)
            return text_chunks
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.warning(
                f"Error creating text chunk for text with url:{url} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                stack_info=True)
            logger.info(f"Skipping the text chunk conversion for the url{url}")
            return []

    @staticmethod
    def generate_embeddings(chunk_list, url=None):
        """
        This method is used to create embedding of the chunk list provided
        Args:
            url:url of the text_chunk
            chunk_list: list of the chunks
        """
        try:
            return embeddings.embed_documents(chunk_list)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.warning(
                f"Error creating embedding for text with url:{url} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                stack_info=True)
            logger.info(f"Skipping the creation of embedding of text chunk for the url{url}")
            return []

    def index_data_to_azure_ai_service(self,last_updated_by):
        """
        Method to index data to azure ai service from Cosmos DB
        """
        try:
            item_url = None
            # get current timestamp
            current_utc_time = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
            data_to_upload_list = []
            sum_empty_chunk = 0

            # get last updated timestamp from Cosmos DB
            last_updated_timestamp = dbops.get_last_updated_timestamp()
            item_list = dbops.get_items(last_updated_timestamp)

            ## if no data found in Cosmos DB then return
            if not item_list:
                logger.info("No data to index in Azure AI Search.")
                return
            latest_modified_news_timestamp = item_list[0]['_ts']
            count = 0
            count_item=0
            for item in item_list:
                try:
                    item_url = item['news_url']
                    item_text = item['news_content']
                    logger.info(f"Processing URL: {item_url}")

                    # create text chunks
                    chunk_list = self.create_text_chunks_list(item_text, item_url)
                    if not chunk_list:
                        continue
                    temp_1 = len(chunk_list)

                    # removing the chunk with the empty whitespace
                    chunk_list = [chunk for chunk in chunk_list if chunk.strip()]
                    temp_2 = len(chunk_list)
                    sum_empty_chunk += temp_1 - temp_2
                    embedding_list = self.generate_embeddings(chunk_list, item_url)

                    # Keeping the client name as "Others" if it is empty
                    if item['client_name'].strip() =="":
                        item['client_name'] = "Others"

                    # Removing embedding for empty chunks
                    if not embedding_list:
                        continue
                    chunk_extended_id = 0
                    for text_chunk, text_embedding in zip(chunk_list, embedding_list):
                        ai_search_data = {
                            "id": item['id'] + "_" + str(chunk_extended_id),
                            "source_name": item['source_name'],
                            "client_name": item["client_name"],
                            "news_url": item["news_url"],
                            "news_title": item["news_title"],
                            "news_date": item["news_date"],
                            "news_content_chunk": text_chunk,
                            "news_summary": item["news_summary"],
                            "sentiment": item["sentiment"].capitalize(),
                            "news_content_chunk_embedding": text_embedding
                        }

                        data_to_upload_list.append(ai_search_data)
                        # append the extended id number
                        count += 1
                        chunk_extended_id += 1

                        # Indexing the items in the batch of 100
                        if count % 100 == 0:
                            logger.info("Indexing data for next 100 chunks")
                            self.search_client.upload_documents(documents=data_to_upload_list)
                            logger.info(f"Indexed data for the total {count} chunks and {count_item} articles")
                            data_to_upload_list = []
                            latest_modified_news_timestamp = item['_ts']
                    count_item += 1
                except  Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    logger.error(f"Skipping the URL: {item_url} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                                 stack_info=True)
                    continue

            else:
                # Indexing the last remaining item
                logger.info("Indexing the last remaining items")
                if not data_to_upload_list:
                    self.search_client.upload_documents(documents=data_to_upload_list)
                latest_modified_news_timestamp = item_list[-1]['_ts']
            logger.info(f"Indexed data for the total {count} chunks and {count_item} articles")


            #saving the lst article timestamp in the database
            dbops.save_new_timestamp(latest_modified_news_timestamp, current_utc_time,last_updated_by)
            logger.info("AI Search indexing completed successfully")

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error Indexing data in Azure AI Search.Line No: {exc_tb.tb_lineno}"
                           f"  Error: {str(e)}", stack_info=True)
            raise Exception

    @staticmethod
    async def async_trigger_http_function(last_updated_by, url=os.environ["AZURE_FUNCTION_URL"]):
        """
        This function makes an async HTTP POST request to trigger an Azure Function.

        Args:
            url (str): The URL of the Azure Function to be triggered.
            last_updated_by (str): The name of the service that triggered the Azure Function.

        Returns:
            None
        """
        # Create a session for the HTTP client
        try:
            # Create a dictionary to store the data to be sent in the request body
            data_dict = {"triggered_by":last_updated_by}

            # Create an async HTTP client session
            async with aiohttp.ClientSession() as client:
                # Send a POST request to the specified URL with the data
                async with client.post(url, json=data_dict) as response:
                    # Log the HTTP status code of the response
                    logger.info(f"Triggered the http function with status code: {response.status}")
                    if response.status != 200:
                        logger.error(f"Failed to trigger the http function with status code: {response.status}")
            # Wait for 10 seconds
            time.sleep(10)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Failed to trigger the http function - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)


