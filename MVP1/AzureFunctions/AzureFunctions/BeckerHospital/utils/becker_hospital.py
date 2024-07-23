"""
Crawler modeule for Becker
"""
import requests
import logging
import html
import sys
from bs4 import BeautifulSoup
from random import randint
import random
from datetime import datetime
from BeckerHospital.utils.becker_summary import get_summary,get_summ_sent_key
from BeckerHospital.utils.becker_db import BeckerDBOPS,KeywordDBOPs
from BeckerHospital.utils.logs import create_log

logger = create_log(name="Becker_Hospital", level=logging.INFO)

db_ops = BeckerDBOPS()

class BeckerCrawl:
    '''
    Class to scrape and summarize becker hopital review data
    '''
    def __init__(self):
        '''
        Init function for scraping becker data
        '''
        self.all_articles_info =[]
        self.failure_cnt=0
        self.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/108.0.0.0 Safari/537.36"
    }

    async def fetch_news_content(self,url):
        '''
        function to scrape the content from the provided url
        params:
            url :- Becker url from which data is to be scraped
        returns:
            scraped text
        '''
        try:
            logger.info(f"Fetching data from {url}")
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                news = soup.get_text(separator=' ')
                title = soup.find('title')
                title=title.string
                return news,title
            else:
                logger.warning(f"Failed to fetch data from {url}. Status code: {response.status_code}")
                return None
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Failed to fetch data from {url}.Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return None

    async def becker_crawling(self,client_name,duration,k_list,scrape_existing=False,
                              persist=True,department_name="Health systems",source_name="Becker Hospital Review"):
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

            response = requests.get(url, headers=self.headers)

            ##Quering the DB for existing urls
            url_list = db_ops.query_url(source_name,client_name)
            # ##quering the keywords
            # k_list = keyword_db_ops.query_keyword_list(department_name)

            if response.status_code == 200:
                # Parse the page with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find all articles
                articles = soup.find_all("li", attrs={"class":"article"})
                # Initialize an empty list to store the dictionaries
                articles_info = []
                #dateformat='%Y-%m-%d:%S'
                dateformat = '%Y-%m-%dT%H:%M:%S.%fZ'
                # Loop through all articles
                for article in articles:
                    # Find the time element (replace 'time' with the actual tag name)
                    time_element = article.find("span", class_="article-date")

                    if time_element is not None:
                        # Get the datetime attribute
                        datetime_str = time_element.text

                        # Parse the datetime string
                        datetime_obj = datetime.strptime(datetime_str, "%d %B %Y")

                        # Format the datetime object
                        date_str = datetime_obj.strftime(dateformat)

                        post_info = article.find("h2", class_="article-title")

                        # Get the href attribute and add "https://www.beckershospitalreview.com"
                        article_link = "https://www.beckershospitalreview.com" + post_info.find("a").get("href")
                        logger.info(f"Extracting information from {article_link}")
                        print(f"Extracting information for {article_link}")
                        
                        ##Checking if the url is already scraped
                        if not scrape_existing and article_link in url_list:
                            logger.info(f"Skipping the scraping for already existing url {article_link}")
                            print(f"Skipping the scraping for already existing url {article_link}")
                            continue

                        ##Get the news content
                        article_news,article_text = await self.fetch_news_content(article_link)

                        #summary
                        llm_response = await get_summ_sent_key(article_news,article_link,client_name,k_list=k_list)

                        # ## Get summary
                        # article_summary = await get_summary(article_news,article_link)
                        print(f"Client relevance {llm_response['client_relevance']} for {article_link}")
                        # Create a dictionary with the href, title, and date
                        if llm_response['client_relevance']:
                            article_dict = {
                                "source_name":source_name,
                                "client_name":client_name,
                                "news_url": article_link,
                                "news_title": article_text,
                                "news_date": date_str,
                                "news_content": article_news,
                                "news_summary": llm_response['summary'],
                                "sentiment":llm_response['sentiment'],
                                "keywords_list":llm_response['matched_keyword_list']
                            }
                            # Append the dictionary to the list
                            articles_info.append(article_dict)
                #print(f"articles_info {articles_info}")
                if persist and articles_info!=[]:
                    logger.info("Saving becker data to db...")
                    print("Saving becker data to db...")
                    db_ops.upsert_items(articles_info)
                return articles_info
            else:
                logger.warning(f"Failed to fetch data from {url}. Status code: {response.status_code}")
                return None
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in scraping the contents Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
