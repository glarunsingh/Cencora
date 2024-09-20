import requests
import os
import logging
import html
import re
from bs4 import BeautifulSoup
import sys
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

#_ = load_dotenv("./BingNews_Plugin/config/config.env")

from config.key_vault import key_vault
secret_value = key_vault()

BING_NEWS_URL = secret_value.get_secret('BING-NEWS-URL') #os.environ['BING_NEWS_URL'] #
BING_SEARCH_URL = secret_value.get_secret('BING-SEARCH-URL') #os.environ['BING_SEARCH_URL'] 
BING_NEWS_KEY =  secret_value.get_secret('BING-NEWS-KEY') #os.environ['BING_NEWS_KEY']

def remove_tags(input_string):
    cleaned_string = re.sub(r'<.*?>', '', input_string)
    return cleaned_string


def bing_news_crawler(search_term, freshness="Month", location="US"):
    """
    Function to extract Bing News using Bing API
    params:
        searchTerm:(text to be searched) - REQUIRED
        freshness: "Day"/"Week"/"Month" from when to get results (Default: Month if not supplied) - OPTIONAL
        location: (get results only for specific location) (Default: US if not supplied) - OPTIONAL

    returns:
        Gets the output in json format
        {
            "title": title,
            "url": url,
            "date": date_published,
            "content": short description given by Bing,
        }
    """
    # BING_NEWS_URL= "https://api.bing.microsoft.com/v7.0/news/search"
    headers = {"Ocp-Apim-Subscription-Key": BING_NEWS_KEY}
    params = {
        # "q":  f'"{search_term}"',
        "q": search_term,
        "freshness": freshness,
        "count": 100,  # Adjust as needed
        "offset": 0,
        "sortBy": "Date",
        # "mkt": location,
        "cc": location,
        "textDecorations": True,
        "textFormat": "HTML"
    }
    try:
        logger.info(f"Starting Bing News Crawling for client {search_term}")
        url_list = []
        # Make multiple requests to get all news articles
        while True:
            response = requests.get(BING_NEWS_URL, headers=headers, params=params)
            search_results = response.json()
            articles = search_results.get("value", [])

            for item in articles:
                name = remove_tags(BeautifulSoup(item.get("name", ""), 'html.parser').get_text())
                url = item.get("url", "")
                description = remove_tags(html.unescape(item.get("description", "")))
                date_published = item.get("datePublished", "")

                # relevant= news_relevance(search_term,name, description)
                # if relevant:
                url_list.append({
                    "title": name,
                    "url": url,
                    "date": date_published,
                    "content": description,
                })
                # else:
                #    print(f"Removing the News as for search term {search_term}, url news is irrelevant {url}")
                #    print(f"{name}")
                #    print(f"{description}")
                #    logger.info(f"Removing the News as for client {search_term}, url news is irrelevant {url}")
            # Check if there are more articles
            if len(articles) < params["count"]:
                break  # No more articles
            # Increment the offset for the next request
            params["offset"] = len(url_list)
        url_list = sorted(url_list, key=lambda x: x['date'], reverse=True)
        logger.info(f"News Crawling Completed for client {search_term}, Total News {len(url_list)}")
        return url_list
    except requests.RequestException as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error fetching data for {search_term} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                    stack_info=True)
        return []


def news_relevance(search_term, title, description):
    """
    Method to detect the news relevance for search term
    """
    synon = search_term.split(" | ")
    alphanumeric_text = re.sub(r"[^\w\s]", "", description.lower())
    relevant = False
    for sterm in synon:
        if re.sub(r"[^\w\s]", "", sterm).lower() in alphanumeric_text:
            relevant = True
        if re.sub(r"[^\w\s]", "", sterm).lower() in re.sub(r"[^\w\s]", "", title).lower():
            relevant = True
        if re.sub(r"[^\w\s]", "", sterm.split(" ")[0]).lower() in alphanumeric_text:
            relevant = True
        if re.sub(r"[^\w\s]", "", sterm.split(" ")[0]).lower() in re.sub(r"[^\w\s]", "", title).lower():
            relevant = True
    return relevant


def bing_search_crawler(search_term, freshness="Month", location="US"):
    """
    Function to extract Bing Search results using Bing API
    params:
        searchTerm:(text to be searched) - REQUIRED
        freshness: "Day"/"Week"/"Month" from when to get results (Default: Month if not supplied) - OPTIONAL
        location: (get results only for specific location) (Default: US if not supplied) - OPTIONAL

    returns:
        Gets the output in json format
        {
            "title": title,
            "url": url,
            "date": date_published,
            "content": short description given by Bing,
        }
    """
    #BING_SEARCH_URL= "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": BING_NEWS_KEY}
    params = {
        "q": search_term,
        "freshness": freshness,
        "count": 100,  # Adjust as needed
        "offset": 0,
        "sortBy": "Date",
        # "mkt": location,
        "cc": location,
        "textDecorations": True,
        "textFormat": "HTML"
    }
    try:
        logger.info(f"Starting Bing News Crawling for client {search_term}")
        url_list = []
        # Make multiple requests to get all news articles
        while True:
            response = requests.get(BING_SEARCH_URL, headers=headers, params=params)
            search_results = response.json()
            articles = search_results.get("webPages", [])['value']

            for item in articles:
                name = remove_tags(BeautifulSoup(item.get("name", ""), 'html.parser').get_text())
                url = item.get("url", "")
                description = remove_tags(html.unescape(item.get("snippet", "")))
                date_published = item.get("datePublished", "")

                # relevant= news_relevance(search_term,name, description)
                # if relevant:
                url_list.append({
                    "title": name,
                    "url": url,
                    "date": date_published,
                    "content": description,
                })
                # else:
                #    print(f"Removing the News as for search term {search_term}, url news is irrelevant {url}")
                #    logger.info(f"Removing the News as for client {search_term}, url news is irrelevant {url}")
            # Check if there are more articles
            if len(articles) < params["count"]:
                break  # No more articles
            # Increment the offset for the next request
            params["offset"] = len(url_list)
        url_list = sorted(url_list, key=lambda x: x['date'], reverse=True)
        logger.info(f"Search Completed for client {search_term}, Total News {len(url_list)}")
        return url_list
    except requests.RequestException as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Error fetching data for {search_term} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                     stack_info=True)
        return []
