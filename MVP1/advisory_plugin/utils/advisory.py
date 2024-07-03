"""
Crawler module for Advisory
"""
import requests
import logging
import html
import sys
from bs4 import BeautifulSoup
import re
from random import randint
import random
from datetime import datetime
from utils.advisory_summary import get_summary,get_summ_sent_key
from utils.advisory_db import AdvisoryDBOPS,KeywordDBOPs
# Set up logging to write to a file
from utils.logs import create_log

logger = create_log(name="Advisory", level=logging.INFO)

db_ops = AdvisoryDBOPS()
keyword_db_ops=KeywordDBOPs()

class AdvisoryCrawl:
    """
    Class to scrape Advisory
    """
    def __init__(self):
        self.all_articles_info =[]
        self.failure_cnt=0
        self.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/108.0.0.0 Safari/537.36"
    }
    def get_content(self,url):
        '''
        function to scrape the content from the provided url
        params:
            url :- advisory url from which data is to be scraped
        returns:
            scraped text
        '''
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            soup= BeautifulSoup(response.text, 'html.parser')
            ##Extracting para tags
            para=soup.find_all('p')
            para_list = [text.text for text in para]
            str_text = "\n".join(para_list)
            #Extracting li tags
            list_text = soup.find_all('li')
            tex_list = [text.text for text in list_text if not re.search('\n',text.text)]
            li_text = "\n".join(tex_list)
            final_str = str_text+li_text
            return final_str
        else:
            logger.info(f"Connection to the url {url} failed  with status_code {response.status_Code}")
            print(f"Connection to the url {url} failed with status_code {response.status_code}")

    async def get_news_data(self,main_url="https://www.advisory.com/daily-briefing/",scrape_existing=False,persist=True,department_name="Health",source_name="advisory"):
        """
        Function to crawl advisory and scrape data
        params:
            main_url: advisory url that needs to be scraped
            source_name: source from which news is to be extracted; in this case advisory
            department: department to which source belongs to
            scrape_existing: Flag , True if existing urls are to scraped again else False;
            persist: Flag , True if the scraped content need to be pushed to DB else False
        returns:
            list of dictionary containing  "source_name":"advisory",
                            "news_url": article_link,
                            "news_title": article_text,
                            "news_date": date_str,
                            "news_content": article_news,
                            "news_summary": llm_response['summary'],
                            "sentiment":llm_response['sentiment'],
                            "keywords_list":llm_response['matched_keyword_list']
        """
        articles_info = []
        dateformat = '%Y-%m-%dT%H:%M:%S.%fZ'
        ##quering the keywords
        k_list = keyword_db_ops.query_keyword_list(department_name)
        ## Quering the existing urls
        url_list = db_ops.query_url(source_name)

        try:
            response = requests.get(main_url,headers=self.headers)
            if response.status_code == 200:
                try:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    news = soup.find_all('a')
                    href =[soup_a.get('href') for soup_a in news]
                    brief_link = ["https://www.advisory.com"+link for link in href if '/daily-briefing' in link and len(link.split('/'))>5]
                    for url in brief_link:
                        ##Check if the url already exist in DB skip the rest
                        if not scrape_existing and url in url_list:
                            logger.info(f"Skipping the scraping for already existing url {url}")
                            print(f"Skipping the scraping for already existing url {url}")
                            continue
                        logger.info(f"Extracting data for {url}")
                        print(f"Extracting data for {url}")
                        text_data=self.get_content(url)
                        sub1 = "Daily Briefing\n"
                        sub2 = "\n\nPosted on"
                        try:
                            # getting index of substrings
                            idx1 = text_data.index(sub1)
                            idx2 = text_data.index(sub2)
                            content = text_data[idx1 + len(sub1) + 1: idx2]
                        except ValueError:
                            content = text_data

                        split_l=url.split('/')
                        title = split_l[-1]
                        date=split_l[-4:-1]
                        date_t="/".join(date)
                        # Parse the datetime string
                        datetime_obj = datetime.strptime(date_t,'%Y/%m/%d').date()
                        # Format the datetime object
                        date_str = datetime_obj.strftime(dateformat)

                        #summary
                        llm_response = await get_summ_sent_key(content,url,k_list=k_list)
                        
                        #source_name	client_name	news_url	news_title	news_date	news_content	news_summary	keywords_list	sentiment
                        article_dict = {
                            "source_name":"advisory",
                            "client_name":'',
                            "news_url": url,
                            "news_title": title,
                            "news_date": date_str,
                            "news_content": content,
                            "news_summary": llm_response['summary'],
                            "sentiment":llm_response['sentiment'],
                            "keywords_list":llm_response['matched_keyword_list']
                        }
                        # Append the dictionary to the list
                        articles_info.append(article_dict)
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    logger.error(f"Error in scraping the contents Line No:"
                                 f" {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            else:
                logger.info(f"Connection to the url {main_url} failed  with status_code {response.status_Code}")
                print(f"Connection to the url {main_url} failed  with status_code {response.status_Code}")
            if persist and len(articles_info)>0:
                logger.info("Saving becker data to db...")
                print("Saving becker data to db...")
                db_ops.upsert_items(articles_info)
            return articles_info
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in scraping the contents Line No:"
                         f" {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)

