import requests
import os
import logging
import html
import re
from bs4 import BeautifulSoup
from datetime import datetime
import sys
from langchain_openai import AzureChatOpenAI
from concurrent.futures import ThreadPoolExecutor
import os
import sys

logger = logging.getLogger(__name__)
from config.key_vault import key_vault
secret_value = key_vault()

class news_summarizer:
    def __init__(self,summary_prompt):
        
        self.summary_prompt=summary_prompt
        
        self.model = AzureChatOpenAI(temperature=0.2,
                    openai_api_key= secret_value.get_secret('AZURE-OPENAI-API-KEY-WEBTOOLS'), #os.getenv("AZURE_OPENAI_API_KEY"),
                    openai_api_version= os.getenv("AZURE_OPENAI_API_VERSION"),
                    azure_deployment= os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                    azure_endpoint = secret_value.get_secret('AZURE-OPENAI-API-ENDPOINT-WEBTOOLS'), #os.getenv("AZURE_OPENAI_ENDPOINT"),
                    verbose=True)
        self.connection_error= False
        try:
            out = self.model.invoke("Write summary on Healthcare")
        except Exception as e:
            if str(e)=="Connection error.":
                print("Open AI API giving connection error, please check before processing further")
                self.connection_error= True
        
        self.output = []
    
    def generate_summary(self, text):       
        try:
            if len(self.summary_prompt)<1:
                logger.info(f"Summary Prompt is empty please provide to summarize")
                return text
            logger.info(f"Starting the News Summarization")
            content_template = f"""{self.summary_prompt}
                -----
                article content: {text} 
                -----
                Avoid section that contains the advertisement and is not related to the article content provided.
                """
            out = self.model.invoke(content_template)
            return out.content
        except Exception as e:
            logger.info(f"Failed to summarize the given content")
            return None
    
    def generate_tsummary(self, url_data):
        
        try:
            logger.info(f"Starting the News Summarization for {url_data['url']}")
            content_template = f"""{self.summary_prompt}
                -----
                article content: {url_data['content']} 
                -----
                Avoid section that contains the advertisement and is not related to the article content provided.
                """
            out = self.model.invoke(content_template)
            if len(out.content)>1:
                    url_data['content']= out.content
            else:
                logger.info(f"Failed to summarize the given content {url_data['url']},{str(out)}") 
            self.output.append(url_data)
            logger.info(f"Completed summarization for the given content {url_data['url']}")
        except Exception as e:
            logger.info(f"Failed to summarize the given content {url_data['url']},{str(e)}")
            self.output.append(url_data)
        
                
    def summarize(self, news_data):
        with ThreadPoolExecutor(max_workers=5) as executor:
            for url_data in news_data:
                executor.submit(self.generate_tsummary, url_data)