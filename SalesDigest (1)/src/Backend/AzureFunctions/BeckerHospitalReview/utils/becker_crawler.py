import re
import requests
from bs4 import BeautifulSoup
from langchain_openai import AzureChatOpenAI
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser
from langchain_core.prompts import PromptTemplate
import pytz
from datetime import datetime
import random
import time
import os
import sys
import logging
from BeckerHospitalReview.utils.database import News_DB
logger = logging.getLogger(__name__)

def utc_date_format(time_element, local_tz, dateformat):
    # Get the datetime attribute
    datetime_str = time_element.text
    # Parse the datetime string
    datetime_obj = datetime.strptime(datetime_str, "%d %B %Y")
    # Converting to UTC time
    local_dt = local_tz.localize(datetime_obj)
    utc_time = local_dt.astimezone(pytz.utc)
    # Format the datetime object
    date_str = utc_time.strftime(dateformat)
    return date_str


def becker_crawling(searchTerm, minDate):
    """
    Method for crawling the Becker News
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/108.0.0.0 Safari/537.36"
        }
        local_tz = pytz.timezone(os.getenv('LOCAL_TIMEZONE'))
        dateformat = '%Y-%m-%dT%H:%M:%S.%fZ'
        duration_l = ["start=20", "start=40", "start=60", "start=80", "start=100", "start=120", "start=140",
                      "start=160", "start=180", "start=200", "start=220", "start=240", "start=260", "start=280",
                      "start=300"]
        final_data = []
        i = 0
        url = f"https://www.beckershospitalreview.com/search.html?searchword={searchTerm}&searchphrase=all"
        while True:

            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all("li", attrs={"class": "article"})
                logger.info(f"Total article for given search term {searchTerm} : {len(articles)}")
                url_list = []
                for article in articles:
                    # Get the href attribute and add "https://www.beckershospitalreview.com"
                    post_endpoint = article.find("h2", class_="article-title")
                    # Skipping if post_endpoint not found
                    if not post_endpoint:
                        logger.info(f"Skipping the article as post endpoint {post_endpoint} not found")
                        continue
                    # Finding the article link
                    article_link = "https://www.beckershospitalreview.com" + post_endpoint.find("a").get("href")

                    time_element = article.find("span", class_="article-date")
                    if time_element:
                        date_str = utc_date_format(time_element, local_tz, dateformat)
                    else:
                        logger.info(f"Skipping the article as time element {time_element} not found")
                        continue
                    title = article.find('h2', class_='article-title').get_text().strip()
                    title = title.replace("\t", "").split('\n')[1]
                    url_list.append({"source_name": "Becker Hospital Review", "client_name": searchTerm,
                                    "news_date": date_str, "news_title": title,
                                    "news_url": article_link})

                if len(url_list) > 0:
                    dates = [item['news_date'] for item in url_list]
                    max_date = max(dates).split("T")[0]
                    if max_date >= minDate:
                        final_data.extend([item for item in url_list if item['news_date'].split("T")[0] >= minDate])
                        duration = duration_l[i]
                        if duration== "start=300":
                            break
                        url = f"https://www.beckershospitalreview.com/search.html?{duration}&searchword={searchTerm}&searchphrase=all"
                        i = i + 1
                        logger.info(f'News Extracted till {min(dates).split("T")[0]} now crawling the Next page')
                        if min(dates).split("T")[0] < minDate:
                            logger.info(f'Stopping the news crawling for given search term {searchTerm}')
                            break
                    else:
                        logger.info(f'Latest news available for given search term {searchTerm} on {max_date}')
                        break
                else:
                    logger.info(f"No News Available for given search term {searchTerm}")
                    break
            else:
                logger.info(f"Response error {response.status_code} for given search term {searchTerm}")
                break
        logger.info(f"Total {len(final_data)} news article for {searchTerm} till time {minDate} found")
        return final_data
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error in crawling news for client {searchTerm}: {exc_tb.tb_lineno}  Error: {str(e)}",
                    stack_info=True)
        return []


def becker_news_prompt():
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


def get_clean_text(soup):
    # Remove unnecessary div elements
    try:
        articles = soup.find("div", id="inner-article-content")

        # Remove unnecessary div elements
        for div in articles.find_all("div", id="topic-to-follow"):
            div.decompose()
        for div in articles.find_all("div", id="latest-articles-outer"):
            div.decompose()

        # Get the clean text from the main article
        text = articles.get_text(separator='')
        # Remove the first and last space of string
        content = text.strip()

        # Remove unnecessary space in between lines
        clean_text = re.sub(r'(\n){3,}', '\n\n', content)
        return clean_text
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Failed to get clean text. Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return None


def becker_news_scrapper(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/108.0.0.0 Safari/537.36"
    }
    try:
        logger.info(f"Fetching data from {url}")
        sleep_time = random.randint(1, 5)
        logger.info(f"Going to sleep to avoid blocking for {sleep_time}s")
        time.sleep(sleep_time)
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            clean_text = get_clean_text(soup)
            if not clean_text or len(clean_text) < 50:
                text = soup.get_text(separator=' ')
                # Remove the first and last space of string
                content = text.strip()
                # Remove unnecessary space in between lines
                clean_text = re.sub(r'(\n){3,}', '\n\n', content)
            return clean_text
        else:
            logger.error(f"Failed to fetch data from {url}")
            return None
    except Exception as e:
        logger.error(f"Failed to fetch data from {url}. Error: {str(e)}")
        return None


def news_output_schema():
    """
    Output parser
    """
    summary_schema = ResponseSchema(name="news_summary",
                                    description="Generate the concise summary of the of given article according to given client.")

    keyword_schema = ResponseSchema(name="matched_keyword_list",
                                    description="Python List of matching keywords from the content based on a list of keywords provided.")

    sentiment_schema = ResponseSchema(name="sentiment",
                                      description="Identify the overall sentiment of the content, whether it is Positive, Negative, or Neutral.")

    breakingnews_schema = ResponseSchema(name="breaking_news",
                                         description="Identify if content is breaking news, \
                                                whether it is true or false.")

    client_schema = ResponseSchema(name="client_relevance",
                                   description="Is the news about the given healthcare client true or false")

    response_schemas = [summary_schema, sentiment_schema, breakingnews_schema, client_schema]
    #response_schemas = [summary_schema, keyword_schema, sentiment_schema, breakingnews_schema,client_schema]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    return output_parser


class BeckerCrawl:
    """
    Main module for Becker news extraction, scrapping and summarization
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
        self.news_db = News_DB()

    def llm_model(self, html_content, client_name):

        retries = 1
        output_dict = {}
        for attempt in range(retries):
            try:
                model = AzureChatOpenAI(temperature=0.2,
                                        openai_api_key=os.environ['AZURE_OPENAI_API_KEY'], #secret_value.get_secret("AZURE-OPENAI-API-KEY"),
                                        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                                        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                                        azure_endpoint= os.environ['AZURE_OPENAI_ENDPOINT'], #secret_value.get_secret("AZURE-OPENAI-ENDPOINT"),
                                        verbose=True)
                news_prompt = becker_news_prompt()
                output_parser = news_output_schema()
                prompt = PromptTemplate(
                    template=news_prompt,
                    input_variables=["raw_content",  "client_name"],
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
            html_content = becker_news_scrapper(url_data['news_url'])
            if html_content is not None:
                alphanumeric_text = re.sub(r"[^\w\s]", "", html_content.lower())
                synon = search_term.split(" | ")
                title = re.sub(r"[^\w\s]", "", url_data['news_title'].lower())
                relevant = False
                for name in synon:
                    #print(name)
                    name = re.sub(r"[^\w\s]", "", name)
                    if name.lower() in alphanumeric_text:
                        relevant = True
                    if name.lower() in title:
                        relevant = True
                    if name.split(" ")[0].lower() in alphanumeric_text:
                        relevant = True
                    if name.split(" ")[0].lower() in title:
                        relevant = True

                #if url_data['client_name'].split(" ")[0] in html_content:
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
                logger.info(
                    f"Scrapping is not successful replacing with for client {url_data['client_name']}- {url_data['news_url']}")

        except Exception as e:
            self.failure_cnt += 1
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(
                f"Error scrapping/summarization url data for client {url_data['client_name']}- {url_data['news_url']}- Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                stack_info=True)
            # raise Exception

    def url_processing(self, client_name, search_term):
        """
        Becker News extraction for given client and scrap/summarize for each url
        """
        self.all_articles_info = []
        self.failure_cnt = 0
        try:
            logger.info(f"Extracting Becker News for Client {client_name}")
            full_urls = becker_crawling(searchTerm=client_name, minDate=self.minDate)
            if self.store_db:
                url_list = self.news_db.query_urls(client_name=client_name, source_name=self.source_name)
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
                logger.info(
                    f"Saving {len(self.all_articles_info)} Becker News data for client {client_name} to Database")
                print(f"Saving {len(self.all_articles_info)} Becker News data for client {client_name} to Database")
                self.news_db.upsert_data(self.all_articles_info)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in Becker News extraction for Client - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)
            # raise Exception
