"""
Crawler module for Becker
"""
import os
import re

import pytz
import requests
import logging
import sys
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from dotenv import load_dotenv

from BeckerHospital.utils.becker_summary import get_summ_sent_key
from BeckerHospital.utils.becker_db import BeckerDBOPS
from BeckerHospital.utils.logs import create_log

logger = create_log(name="Becker_Hospital", level=logging.INFO)
_ = load_dotenv('./BeckerHospital/config/db.env')
db_ops = BeckerDBOPS()


class BeckerCrawl:
    """
    Class to scrape and summarize becker hospital review data
    """

    def __init__(self):
        """
        Init function for scraping becker data
        """
        self.all_articles_info = []
        self.failure_cnt = 0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/108.0.0.0 Safari/537.36"
        }
        current_date = datetime.now()
        self.threshold_date = current_date - timedelta(days=int(os.getenv("BECKER_SCRAPPER_DURATION_DAYS")))

    def get_clean_text(self, soup):
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

    def get_date(self, soup):
        try:
            date_attribute = soup.find_all("time", class_='timeago')
            date_str = date_attribute[0].get('datetime')
            date = date_str[:-1] + ".000000Z"
            return date
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Failed to get date. Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return None

    async def fetch_news_content(self, url):
        """
        function to scrape the content from the provided url
        params:
            url :- Becker url from which data is to be scraped
        returns:
            scraped text
        """
        try:
            logger.info(f"Fetching data from {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                clean_text = self.get_clean_text(soup)
                if not clean_text or len(clean_text) < 50:
                    text = soup.get_text(separator=' ')
                    # Remove the first and last space of string
                    content = text.strip()
                    # Remove unnecessary space in between lines
                    clean_text = re.sub(r'(\n){3,}', '\n\n', content)

                # Get article title
                title = soup.find('title')
                title = title.string

                # Get article date
                date = self.get_date(soup)

                return clean_text, title, date
            else:
                logger.warning(f"Failed to fetch data from {url}. Status code: {response.status_code}")
                return None, None, None
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Failed to fetch data from {url}.Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)
            return None, None, None

    async def becker_crawling(self, client_name, duration, k_list, scrape_existing=True,
                              persist=True, department_name="Health systems", source_name="Becker Hospital Review"):
        """
        Function to crawl becker and scrape data for the provided client
        params:
            source_name: source from which news is to be extracted; in this case Becker review hospital
            client: search keyword or client name for which data is to be extracted
            duration: Optional ,default:all
            department: department to which source belongs to
            scrape_existing: Flag , True if existing urls are to scraped again else False;
            persist: Flag , True if the scraped content need to be pushed to DB else False
        returns:
            list of dictionary containing  "source_name":"becker review hospital",
                            "client_name":client_name,
                            "news_url": article_link,
                            "news_title": article_text,
                            "news_date": date_str,
                            "news_content": article_news,
                            "news_summary": llm_response['summary'],
                            "sentiment":llm_response['sentiment'],
                            "keywords_list":llm_response['matched_keyword_list']
        """
        try:
            if duration == "all":
                url = f"https://www.beckershospitalreview.com/search.html?searchword={client_name}&searchphrase=all"
            elif 'start' in duration:
                url = f"https://www.beckershospitalreview.com/search.html?{duration}&searchword={client_name}&searchphrase=all"
            else:
                url = f"https://www.beckershospitalreview.com/search.html?searchword={client_name}&when%3A{duration}&searchphrase=all"

            logger.info(f"Extracting information from {url}")
            response = requests.get(url, headers=self.headers, timeout=15)

            # Querying the DB for existing urls
            url_list = db_ops.query_url(source_name, client_name)
            # Querying the keywords
            # k_list = keyword_db_ops.query_keyword_list(department_name)

            if response.status_code == 200:
                # Parse the page with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find all articles
                articles = soup.find_all("li", attrs={"class": "article"})
                # Initialize an empty list to store the dictionaries
                articles_info = []
                #dateformat='%Y-%m-%d:%S'
                dateformat = '%Y-%m-%dT%H:%M:%S.%fZ'
                # Loop through all articles
                for article in articles:
                    # Get the href attribute and add "https://www.beckershospitalreview.com"
                    post_endpoint = article.find("h2", class_="article-title")

                    # Skipping if post_endpoint not found
                    if not post_endpoint:
                        logger.info("Skipping the article as post_endpoint not found")
                        continue

                    # Finding the article link
                    article_link = "https://www.beckershospitalreview.com" + post_endpoint.find("a").get("href")
                    logger.info(f"Extracting information from {article_link}")

                    # Skipping the article if time element is not found
                    # Find the time element (replace 'time' with the actual tag name)
                    time_element = article.find("span", class_="article-date")
                    if time_element:
                        # Get the datetime attribute
                        datetime_str = time_element.text
                        # Parse the datetime string
                        datetime_obj = datetime.strptime(datetime_str, "%d %B %Y")
                        # Converting to UTC time
                        local_tz = pytz.timezone(os.getenv('LOCAL_TIMEZONE'))
                        local_dt=local_tz.localize(datetime_obj)
                        utc_time = local_dt.astimezone(pytz.utc)

                        # Format the datetime object
                        date_str = utc_time.strftime(dateformat)

                    # Check if the article date is older than the scrapping duration
                    if datetime_obj < self.threshold_date:
                        logger.info(
                            f"Skipping the URL as it is older than the scrapping duration {self.threshold_date} for "
                            f"URL: {article_link}")
                        continue

                    # Checking if the url is already scraped
                    if not scrape_existing and article_link in url_list:
                        logger.info(f"Skipping the scraping for already existing url {article_link}")
                        continue

                    # Get the news content
                    article_news, article_text, article_date = await self.fetch_news_content(article_link)
                    # If unable to find the date in the news content page then the page containing the news list date
                    # for the article will be taken
                    if article_date:
                        article_date = date_str

                    if article_news and article_text and article_date:
                        # Summary, sentiment and keywords
                        llm_response = await get_summ_sent_key(article_news, article_link, client_name,
                                                               k_list=k_list)

                        # ## Get summary
                        # article_summary = await get_summary(article_news,article_link)
                        logger.info(
                            f"Client relevance {llm_response['client_relevance']} {type(llm_response['client_relevance'])} {llm_response['sentiment']}  for {article_link}")  # Create a dictionary with the href, title, and date
                        if llm_response['client_relevance'] in ['True', 'true', True]:
                            article_dict = {
                                "source_name": source_name,
                                "client_name": client_name,
                                "news_url": article_link,
                                "news_title": article_text,
                                "news_date": article_date,
                                "news_content": article_news,
                                "news_summary": llm_response['summary'],
                                "sentiment": llm_response['sentiment'],
                                "keywords_list": llm_response['matched_keyword_list']
                            }
                            # Append the dictionary to the list
                            articles_info.append(article_dict)
                        else:
                            logger.info(
                                f"Client Relevance: {llm_response['client_relevance']} Skipping {article_link} ")
                # print(f"articles_info {articles_info}")
                if persist and articles_info != []:
                    logger.info("Saving becker data to db...")
                    db_ops.upsert_items(articles_info)
                return articles_info
            else:
                logger.warning(f"Failed to fetch data from {url}. Status code: {response.status_code}")
                return None
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in scraping the contents Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)
            return None
