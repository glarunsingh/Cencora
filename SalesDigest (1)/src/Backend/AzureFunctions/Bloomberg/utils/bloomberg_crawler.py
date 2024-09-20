import re
import requests
from bs4 import BeautifulSoup
from langchain_openai import AzureChatOpenAI
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser
from langchain_core.prompts import PromptTemplate
import time
import pytz
from datetime import datetime
import dateutil.parser
import os
import logging
import sys

logger = logging.getLogger(__name__)

AZURE_OPENAI_API_KEY= os.environ['AZURE_OPENAI_API_KEY']
AZURE_OPENAI_API_VERSION=os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT=os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_ENDPOINT= os.environ['AZURE_OPENAI_ENDPOINT']
LOCAL_TIMEZONE = pytz.timezone(os.getenv('LOCAL_TIMEZONE'))

from Bloomberg.utils.database import News_DB

def utc_date_format(time_element, local_tz, dateformat):
    # Parse the datetime string
    #datetime_obj= datetime.strptime(time_element, '%B %d, %Y %I:%M %p')
    datetime_obj = dateutil.parser.parse(time_element)
    # Converting to UTC time
    local_dt = local_tz.localize(datetime_obj)
    utc_time = local_dt.astimezone(pytz.utc)
    # Format the datetime object
    date_str = utc_time.strftime(dateformat)
    return date_str

def remove_tags(input_string):
    cleaned_string = re.sub(r'<.*?>', '', input_string)
    return cleaned_string

def news_crawler():
    """
    Method to extract bloomberg news for given search term and date
    """
    # Define the URL and payload
    url = "https://about.bgov.com/news/"
    try:
        logger.info(f"Starting Bloomberg News Crawling")
        # Send a GET request to the URL
        response = requests.get(url,timeout=240)
        if response.status_code == 200:
            url_list = []
            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
        
            # Find all teaser news containers
            teaser_divs = soup.find_all('div', class_='teaser news ft-container')
            if len(teaser_divs) > 0:
                for teaser in teaser_divs:
                    # Find the <a> tags within each teaser
                    a_tags = teaser.find_all('a', href=True)   
                    for a in a_tags:
                        if a['href'] not in url_list:
                            url_list.append(a['href'])
            else:
                logger.info(f"No News available for Bloomberg")

            logger.info(f"News Crawling Completed for Bloomberg, Total News {len(url_list)}")
            return url_list
        else:
            logger.info(f"Unable to connect to with Bloomberg URL {response.status_code} ")
            return []
    except requests.RequestException as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error fetching data form Bloomberg - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                    stack_info=True)
        return []
    
def text_cleaning(result_string):
    """
    Method to clean the content
    """
    cleaned_text = re.sub(r'\xa0', ' ', result_string)
    cleaned_text = re.sub(r'\r', '\n', cleaned_text)
    cleaned_text = re.sub(r"(\n)+", '\n', cleaned_text)
    cleaned_text= cleaned_text.split("\nAlso Read")[0]
    cleaned_text= cleaned_text.split("Read More")[0]
    cleaned_text =  cleaned_text.split("Login »")[0]
    cleaned_text =  cleaned_text.split("©")[0]
    cleaned_text =  cleaned_text.split("\ntwitter")[0]
    cleaned_text =  cleaned_text.split("More Local News >")[0]
    cleaned_text =  cleaned_text.split("More Spotlight >")[0]
    cleaned_text =  cleaned_text.split("Post a Comment")[0]
    cleaned_text = re.sub(r'Click here to Subscribe', ' ', cleaned_text)
    cleaned_text = re.sub(r'Click here to Login', ' ', cleaned_text) 
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    return cleaned_text
    
def news_scrapper(url,source_name):
    """
    Method to scrap the given url using request call and beautiful soup
    """
    headers= {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/108.0.0.0 Safari/537.36"
    }
    try:
        #logger.info(f"Fetching data from {url}")
        response = requests.get(url, headers=headers,timeout= 200)
        if response.status_code == 200:
            url_data = {"source_name": source_name,
                        "client_name": "",
                        "news_url": url}
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the title
            title_tag = soup.find('h1', class_='news__header__title')
            url_data['news_title'] = title_tag.get_text(strip=True) if title_tag else 'No title found'
            
            # Extract the date
            dateformat = '%Y-%m-%dT%H:%M:%S.%fZ'
            time_tag = soup.find('time')
            time_element = time_tag.get_text(strip=True)
            url_data['news_date'] = utc_date_format(time_element, LOCAL_TIMEZONE, dateformat)
            
            # Extract the article body
            content_div = soup.find('div', class_='news__content')
            paragraphs = content_div.find_all('p') 
    
            if len(paragraphs) > 0:
                result_string = ""
                for p in paragraphs:
                    result_string +=f"{p.get_text(separator=' ')}\n"
                    
                if len(result_string)< 0.05*len(content_div.get_text()):
                    logger.info(f"paragraphs text is very less compare to full content extracting the full text  {url}: {result_string} ")
                    result_string = content_div.get_text()

                url_data['news_content'] = text_cleaning(result_string)
                return url_data
            else:
                news = content_div.get_text(separator=' ')
                url_data['news_content'] = text_cleaning(news)
                logger.info(f"No paragraphs found in data using direct get_text method  {url}")
                return url_data
        else:
            logger.info(f"Failed to fetch data from {url}. Error: {str(response.status_code)}")
            return None
            
    except Exception as e:
        logger.info(f"Failed to fetch data from {url}. Error: {str(e)}")
        return None

def bloomberg_news_prompt():
    """
    prompt definition
    """

    content_template = """You are a Sales Manager of a Multinational Corporation in Life Science Domain. Your role is
    to generate the concise summary for given article content.Also identify the sentiments from the given content. 
    You also need to extract matching keywords from the content based on a list of keywords you are provided. 
    You will be provided with following information:
    -----
        article content: ''' {raw_content} ''' and
        keyword list: ''' {keywords_list} '''
    -----
    ---------------
    Response Instructions:
    1. Generate the concise summary of the given article content.
    2. Identify the overall sentiment of the article content, it should be either Positive, Negative, or 
        Neutral.
    3. List of matching keywords from the given article content based on a list of keywords provided.

    Avoid section that contains the advertisement and is not related to the article content provided.

    {format_instructions}
    """
    return content_template

def news_output_schema():
    """
    Output parser
    """
    summary_schema = ResponseSchema(name="news_summary",
                                    description="Generate the concise summary of the of given article content")

    sentiment_schema = ResponseSchema(name="sentiment",
                                    description="Identify the overall sentiment of the content, whether it is Positive, Negative, or Neutral.")
    keyword_schema = ResponseSchema(name="matched_keyword_list",
                                    description="Python List of matching keywords from the content based on a list of keywords provided.")

    response_schemas = [summary_schema, sentiment_schema,keyword_schema]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    return output_parser

class BloombergCrawl:
    """
    Main module for Bloomberg news extraction, scrapping and summarization
    """

    def __init__(self, department_name, source_name, store_db):

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/108.0.0.0 Safari/537.36"
        }
        self.department_name = department_name
        self.source_name = source_name
        self.store_db = store_db
        self.news_db = News_DB()
        self.keyword_list = self.news_db.query_keyword_list(department_name=self.department_name)

    def llm_model(self, html_content):
       
        retries = 1
        output_dict = {}
        for attempt in range(retries):
            try:
                #print(html_content)
                model = AzureChatOpenAI(temperature=0.2,
                                        openai_api_key= AZURE_OPENAI_API_KEY,
                                        openai_api_version=AZURE_OPENAI_API_VERSION,
                                        azure_deployment= AZURE_OPENAI_DEPLOYMENT,
                                        azure_endpoint= AZURE_OPENAI_ENDPOINT,
                                        verbose=True)
                news_prompt = bloomberg_news_prompt()
                #print(news_prompt)
                output_parser = news_output_schema()
                prompt = PromptTemplate(
                    template=news_prompt,
                    input_variables=["raw_content", "keywords_list"],
                    partial_variables={"format_instructions": output_parser.get_format_instructions()}
                )
                chain = prompt | model | output_parser
                output_dict = chain.invoke(
                    {"raw_content": html_content, "keywords_list": self.keyword_list})
                #print(output_dict)
                logger.info(f"Summarization for given content is successful")
                return output_dict
            except Exception as e:
                logger.info(f"LLM Model is failing for given article")
                logger.info(f"Error: {e}")
                logger.info(f"Retrying ({attempt + 1}/{retries})...")
                time.sleep(2)  # Add a sleep interval (e.g., 1 second) between retries
        return output_dict

    def news_summary(self, url):
        """
        Method to scrap the data and summarize
        """
        logger.info(f"News Scrapping for URL - {url}")
        try:
            url_data = news_scrapper(url,self.source_name)
            if url_data is not None:
                output_dict = {}
                output_dict = self.llm_model(url_data['news_content'])
                #print(output_dict)
                if len(output_dict) > 0:
                    url_data['news_summary'] = output_dict['news_summary']
                    url_data['sentiment'] = output_dict['sentiment']
                    url_data['keywords_list'] = output_dict['matched_keyword_list']
                    self.all_articles_info.append(url_data)
                else:
                    self.failure_cnt += 1
                    logger.info(f"LLM model failed to Summarize- {url_data['news_url']}")
            else:
                self.failure_cnt += 1
                logger.info(f"Error in Scrapping data - {url}")
        except Exception as e:
            self.failure_cnt += 1
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(
                f"Error scrapping/summarization url {url}- Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                stack_info=True)

    def url_processing(self):
        """
        Bloomberg News extraction and scrap/summarize for each url
        """
        self.all_articles_info = []
        self.failure_cnt = 0
        try:
            logger.info(f"Extracting Bloomberg News")
            full_urls = news_crawler()
            if self.store_db:
                url_list = self.news_db.query_urls(source_name=self.source_name)
                filtered_items = [item for item in full_urls if item not in url_list]
            else:
                filtered_items = full_urls
            print(f"For {len(full_urls) - len(filtered_items)} out of {len(full_urls)} Data is available in DB")
            logger.info(f"For {len(full_urls) - len(filtered_items)} out of {len(full_urls)} Data is available in DB")

            for news_url in filtered_items:
                print(news_url)
                logger.info(f"Starting for {news_url} ")
                self.news_summary(news_url)

            logger.info(
                f"News Crawling Completed for Bloomberg, Total News {len(full_urls)}, Failed {self.failure_cnt}")
            if self.store_db and len(self.all_articles_info) > 0:
                print(self.all_articles_info[0])
                logger.info(f"Saving {len(self.all_articles_info)} Bloomberg News data to Database")
                self.news_db.upsert_data(self.all_articles_info)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in Bloomberg News extraction - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                        stack_info=True)
