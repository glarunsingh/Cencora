import re
import requests
from bs4 import BeautifulSoup
from langchain_openai import AzureChatOpenAI
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser
from langchain_core.prompts import PromptTemplate
import time
import os
import logging
import sys
from BingNews.utils.database import Bing_News_DB

logger = logging.getLogger(__name__)

VERIFY_VALUE= True #False #os.getenv("VERIFY_VALUE",True)
BING_NEWS_Plugin_URL = os.environ['BING_NEWS_PlUGIN_URL'] #secret_value.get_secret('BING-NEWS-PlUGIN-URL')
SCRAPE_PLUGIN_URL = os.environ['SCRAPE_PLUGIN_URL'] #secret_value.get_secret('SCRAPE-PLUGIN-URL')

def remove_tags(input_string):
    cleaned_string = re.sub(r'<.*?>', '', input_string)
    return cleaned_string


def bing_news_crawler(client_name, search_term, minDate, location="US"):
    """
    Method to extract bing news for given search term and date
    """
    # Define the URL and payload
    bing_url = BING_NEWS_Plugin_URL
    payload = {
        "searchType": "News",
        "maxResults": 1000,
        "scrape": False,
        "summarize": False,
        "summaryPrompt": "",
        "searchTerm": search_term,
        "location": location,
        "minDate": minDate
    }
    print(payload)
    try:
        logger.info(f"Starting Bing News Crawling for client {search_term}")
        url_list = []
        # Make multiple requests to get all news articles
        if os.environ['PROD']=="True":
            response = requests.post(bing_url,headers={"api-key": f"{os.environ['PROD_BING_PLUGIN_KEY']}"}, json=payload, timeout=240)
        else:
            response = requests.post(bing_url, json=payload,timeout=240, verify=VERIFY_VALUE)
        if response.status_code == 200:
            search_results = response.json()
            articles = search_results['data']
            if len(articles) > 0:
                for item in articles:
                    url_list.append({
                        "source_name": "Bing News",
                        "client_name": client_name,
                        "news_title": item['title'],
                        "news_date": item['date'],
                        "news_url": item['url'],
                        "description": item['content']
                    })
            logger.info(f"News Crawling Completed for client {search_term}, Total News {len(url_list)}")
            return url_list
        else:
            logger.info(f"Unable to connect to Plugins {response.status_code} ")
            return []
    except requests.RequestException as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error fetching data for {search_term} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                    stack_info=True)
        return []


def bing_news_prompt():
    """
    prompt definition
    """

    content_template = """You are a Sales Manager of a Multinational Corporation in Life Science Domain. Your role is
    to generate the concise summary for given article content according to given client. Also identify the sentiments from the given content. 
     Also identify the content is breaking news and identify the content is about the
    given is about given client or not, it should be from Healthcare industry.
    You will be provided with following information:
    -----
        article content: ''' {raw_content} ''' and 
        client:'''{client_name}'''
    -----
    ---------------
    Response Instructions:
    1. Generate the concise summary of the article scrapped should be specific to given client.
    2. Identify the overall sentiment of the article scrapped content, it should be either Positive, Negative, or 
        Neutral.
    3. Is Breaking news true, or false
    4. Is News is about the given client, client should be from Healthcare industry only true, or false

    Avoid section that contains the advertisement and is not related to the article content provided.

    {format_instructions}
    """
    return content_template


#

def news_scrapper(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/108.0.0.0 Safari/537.36"
    }
    try:
        logger.info(f"Fetching data from {url}")
        response = requests.get(url, headers=headers, timeout=10,verify=VERIFY_VALUE)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # The above code is a comment in Python. Comments are used to provide explanations or
            # notes within the code and are not executed by the interpreter. In this case, the comment
            # is indicating that the following text is a series of paragraphs.
            paragraphs = soup.find_all('p')  #check other tags for paragraphs
            if len(paragraphs) > 0:

                result_string = ""
                for p in paragraphs:
                    result_string += f"{p.get_text(separator=' ')}\n"

                    if len(result_string) < 0.05 * len(soup.get_text()):
                        result_string = soup.get_text()

                return result_string

            else:
                logger.error(f"No paragraphs found in data from {soup.get_text(separator=' ').strip()}")
                return None
        else:
            logger.error(f"Failed to fetch data from {url}")
            return None
    except Exception as e:
        logger.error(f"Failed to fetch data from {url}. Error: {str(e)}")
        return None


def bing_news_output_schema():
    """
    Output parser
    """
    summary_schema = ResponseSchema(name="news_summary",
                                    description="Generate the concise summary of the of given article according to "
                                                "given client.")

    keyword_schema = ResponseSchema(name="matched_keyword_list",
                                    description="Python List of matching keywords from the content based on a list of "
                                                "keywords provided.")

    sentiment_schema = ResponseSchema(name="sentiment",
                                      description="Identify the overall sentiment of the content, whether it is "
                                                  "Positive, Negative, or Neutral.")

    breakingnews_schema = ResponseSchema(name="breaking_news",
                                         description="Identify if content is breaking news, \
                                                whether it is true or false.")

    client_schema = ResponseSchema(name="client_relevance",
                                   description="Is the news about the given healthcare client true or false")

    response_schemas = [summary_schema, sentiment_schema, breakingnews_schema, client_schema]
    # response_schemas = [summary_schema, keyword_schema, sentiment_schema, breakingnews_schema,client_schema]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    return output_parser


class BingCrawl:
    """
    Main module for bing news extraction, scrapping and summarization
    """

    def __init__(self, source_name, minDate, location, store_db):

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/108.0.0.0 Safari/537.36"
        }
        self.source_name = source_name
        self.minDate = minDate
        self.location = location
        self.store_db = store_db

        self.bing_news_db = Bing_News_DB()
        #self.keyword_list = self.bing_news_db.query_keyword_list(department_name=self.department_name)

    def llm_model(self, html_content, client_name):

        retries = 1
        output_dict = {}
        for attempt in range(retries):
            try:
                model = AzureChatOpenAI(temperature=0.2,
                                        openai_api_key= os.environ['AZURE_OPENAI_API_KEY'],  #secret_value.get_secret("AZURE-OPENAI-API-KEY"),
                                        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                                        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                                        azure_endpoint= os.environ['AZURE_OPENAI_ENDPOINT'],  #secret_value.get_secret("AZURE-OPENAI-ENDPOINT"),
                                        verbose=True)
                news_prompt = bing_news_prompt()
                output_parser = bing_news_output_schema()
                prompt = PromptTemplate(
                    template=news_prompt,
                    input_variables=["raw_content", "client_name"],
                    partial_variables={"format_instructions": output_parser.get_format_instructions()}
                )
                chain = prompt | model | output_parser
                output_dict = chain.invoke(
                    {"raw_content": html_content, "client_name": client_name})
                logger.info(f"Summarization for given content is successful")
                return output_dict
            except Exception as e:
                logger.info(f"LLM Model is failing for {client_name}")
                logger.info(f"Error: {e}")
                logger.info(f"Retrying ({attempt + 1}/{retries})...")
                time.sleep(2)  # Add a sleep interval (e.g., 1 second) between retries
        return output_dict

    def news_summary(self, url_data, search_term):
        """
        Method to scrap the data and summarize
        """
        logger.info(f"News Scrapping for URL - {url_data['news_url']}")
        try:
            # html_content = news_scrapper(url_data['news_url'])   ########## replace with web App
            payload = {
                "url": url_data['news_url'],
                "summarize": False,
                "summaryPrompt": ""
            }

            # Make a POST request
            if os.environ['PROD']=="True":
                response = requests.post(SCRAPE_PLUGIN_URL,headers={"api-key": f"{os.environ['PROD_BING_PLUGIN_KEY']}"}, json=payload, timeout=240)
            else:
                response = requests.post(SCRAPE_PLUGIN_URL, json=payload, timeout=240,verify=VERIFY_VALUE)
            
            if response.status_code == 200:
                search_results = response.json()
                scrapped_data = search_results['data']
                if len(scrapped_data) > 0:
                    html_content = scrapped_data['content']
                if html_content is None:
                    html_content = url_data['description']
                    logger.info(
                        f"Scrapping is not successful replacing with Bing Snippet for client {url_data['client_name']}- {url_data['news_url']}")
                if len(html_content) < 0.5 * len(url_data['description']):
                    html_content = url_data['description']
                    logger.info(
                        f"Scrapping is not successful replacing with Bing Snippet for client {url_data['client_name']}- {url_data['news_url']}")

                alphanumeric_text = re.sub(r"[^\w\s]", "", html_content.lower())
                synon = search_term.split(" | ")
                title = re.sub(r"[^\w\s]", "", url_data['news_title'].lower())
                relevant = False
                for name in synon:
                    # print(name)
                    name = re.sub(r"[^\w\s]", "", name)
                    if name.lower() in alphanumeric_text:
                        relevant = True
                    if name.lower() in title:
                        relevant = True
                    if name.split(" ")[0].lower() in alphanumeric_text:
                        relevant = True
                    if name.split(" ")[0].lower() in title:
                        relevant = True

                # if url_data['client_name'].split(" ")[0] in html_content:
                if relevant:
                    output_dict = {}
                    output_dict = self.llm_model(html_content, url_data['client_name'])
                    if len(output_dict) > 0 and output_dict['client_relevance'] == "true":
                        url_data['news_content'] = html_content
                        url_data['news_summary'] = output_dict['news_summary']
                        url_data['sentiment'] = output_dict['sentiment']
                        url_data['breaking_news'] = output_dict['breaking_news']
                        self.all_articles_info.append(url_data)
                    else:
                        self.failure_cnt += 1
                        logger.info(
                            f"After Gen AI Exploration URL is irrelevant for client{url_data['client_name']}- {url_data['news_url']}")
                else:
                    self.failure_cnt += 1
                    logger.info(f"URL is irrelevant for client{url_data['client_name']}- {url_data['news_url']}")
            else:
                self.failure_cnt += 1
                logger.info(f"Unable to connect to Scrape Plugin {response.status_code}")
        except Exception as e:
            self.failure_cnt += 1
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(
                f"Error scrapping/summarization url data for client {url_data['client_name']}- {url_data['news_url']}- Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                stack_info=True)
            # raise Exception

    def url_processing(self, client_name, search_term):
        """
        Bing News extraction for given client and scrap/summarize for each url
        """
        self.all_articles_info = []
        self.failure_cnt = 0
        try:
            logger.info(f"Extracting Bing News for Client {client_name}")
            #full_urls = bing_news_crawler(client_name= client_name,search_term=search_term, freshness= self.duration,location=self.location)
            full_urls = bing_news_crawler(client_name=client_name, search_term=search_term, minDate=self.minDate,
                                          location=self.location)
            if self.store_db:
                url_list = self.bing_news_db.query_urls(client_name=client_name, source_name=self.source_name)
                filtered_items = [item for item in full_urls if item['news_url'] not in url_list]
            else:
                filtered_items = full_urls

            logger.info(f"For {len(full_urls) - len(filtered_items)} out of {len(full_urls)} Data is available in DB")

            for url_data in filtered_items:
                logger.info(f"Starting for {url_data['news_url']} ")
                self.news_summary(url_data, search_term)

            logger.info(
                f"News Crawling Completed for client {client_name}, Total News {len(full_urls)}, Failed {self.failure_cnt}")
            if self.store_db and len(self.all_articles_info) > 0:
                print(self.all_articles_info[0])
                logger.info(f"Saving {len(self.all_articles_info)} Bing News data for client {client_name} to Database")
                print(f"Saving Bing News data for client {client_name} to Database")
                self.bing_news_db.upsert_data(self.all_articles_info)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in Bing News extraction for Client - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)
            # raise Exception
