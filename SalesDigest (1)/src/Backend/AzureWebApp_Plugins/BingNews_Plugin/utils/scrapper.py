import requests
import logging

import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
def news_relevance(search_term,title, description):
    """
    Method to detect the news relevance for search term
    """
    synon = search_term.split(" | ")
    alphanumeric_text = re.sub(r"[^\w\s]", "", description.lower())
    relevant= False
    for sterm in synon:
        if re.sub(r"[^\w\s]", "", sterm).lower() in alphanumeric_text:
            relevant= True
        if re.sub(r"[^\w\s]", "", sterm).lower() in re.sub(r"[^\w\s]", "", title).lower():
            relevant= True
        if re.sub(r"[^\w\s]", "", sterm.split(" ")[0]).lower() in alphanumeric_text:
            relevant= True
        if re.sub(r"[^\w\s]", "", sterm.split(" ")[0]).lower() in re.sub(r"[^\w\s]", "", title).lower():
            relevant= True
    return relevant

def text_cleaning(result_string):
    """
    Method to clean the content
    """
    cleaned_text = re.sub(r'\xa0', ' ', result_string)
    cleaned_text = re.sub(r'\r', '\n', cleaned_text)
    cleaned_text = re.sub(r"(\n)+", '\n', cleaned_text)
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
    
def news_scrapper(url):
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
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')   #check other tags for paragraphs
            #paragraphs.extend(soup.find_all('div', {'class': 'post hentry'}))
            if len(paragraphs) > 0:
                result_string = ""
                for p in paragraphs:
                    result_string +=f"{p.get_text(separator=' ')}\n"
                    
                if len(result_string)< 0.05*len(soup.get_text()):
                    #print(f"paragraphs text is very less compare to full content extracting the full text  {url}: {result_string} ")
                    logger.info(f"paragraphs text is very less compare to full content extracting the full text  {url}: {result_string} ")
                    result_string = soup.get_text()

                cleaned_text = text_cleaning(result_string)
                return cleaned_text
            else:
                news = soup.get_text(separator=' ')
                news = text_cleaning(news)
                #print(f"No paragraphs found in data using direct get_text method  {url} {news}")
                logger.info(f"No paragraphs found in data using direct get_text method  {url} {news}")
                return news
        else:
            print(f"Failed to fetch data from {url}. Error: {str(response.status_code)}")
            logger.info(f"Failed to fetch data from {url}. Error: {str(response.status_code)}")
            return None
            
    except Exception as e:
        #print(f"Failed to fetch data from {url}. Error: {str(e)}")
        logger.info(f"Failed to fetch data from {url}. Error: {str(e)}")
        return None
    
def all_scrapper(result_data):
    return_data=[]
    try:
        def news_scraping(url_data):
            logger.info(f"Starting the News Scrapping for {url_data['url']}")
            scrape_data= news_scrapper(url_data["url"])
            if scrape_data is not None and len(scrape_data)>len(url_data["content"]):
                url_data["content"] = scrape_data
                return_data.append(url_data)
                logger.info(f"Completed the News Scrapping for {url_data['url']}")
            else:
                logger.info(f"Failed to scrap data for url: {url_data['url']} keeping the original bing content")
                return_data.append(url_data)
        with ThreadPoolExecutor(max_workers=5) as executor:
            for url_data in result_data:
                executor.submit(news_scraping, url_data)
        return return_data
                
    except Exception as e:
        logger.info(f"Failed to scarp data. Error: {str(e)}")
        return result_data