import logging
import re
import sys

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

from utils.logs import create_log
from utils.summarizer import get_sum_key_sent, llm_content_sum_key_sent
from utils.url_parameters import url_headers, read_timeout

logger = create_log(name="HIMSS", level=logging.INFO)

async def get_news_items(url):
    """
    Fetches news articles from the given URL and returns a list of relevant news items.
    
    Args:
        url (str): URL of the news page.
    
    Returns:
        list: List of tuples containing (article_date, full_url).
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Error fetching the URL! Url: {url} Request status code: {response.status_code}")
        return None, None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    exclude_urls = {
        "https://www.himss.org/news/mobihealthnews",
        "https://www.himss.org/news/michigan-healthcare-it-news",
        "https://www.himss.org/news/healthcare-finance-news",
        "https://www.himss.org/news/himss-tv"
    }
    
    news_items = []
    for article in soup.find_all('div', class_='mb-5 grid-12 card-list views-row'):
        date_div = article.find('div', class_='date')
        url_div = article.find('a', href=True)
        
        if date_div and url_div:
            date_text = date_div.get_text(strip=True)
            try:
                article_date = datetime.strptime(date_text, '%B %d, %Y')
            except ValueError as e:
                print(f"Error parsing date: {e}")
                continue
            href = url_div['href']
            
            full_url = f"https://www.himss.org{href}"
            if full_url not in exclude_urls:
                news_items.append((article_date, full_url))
    
    news_items.sort(key=lambda x: x[0], reverse=True)
    return news_items

def extract_news_content(news_link):
    """
    Extracts the main content of a news article from the given URL.
    
    Args:
        news_link (str): URL of the news article.
    
    Returns:
        str: Extracted content text.
    """
    try:
        news_response = requests.get(news_link)
        news_response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Error fetching the news article: {e}")
        return None, None

    news_soup = BeautifulSoup(news_response.content, 'html.parser')
    
    news_topic = news_soup.find('h1', class_='white')
    news_topic_text = news_topic.get_text(strip=True) if news_topic else "No title found"
    
    content_div = news_soup.find('div', class_='field-body')
    content_text = content_div.get_text(strip=True, separator=' ') if content_div else "No content found"
    
    return news_topic_text, content_text

def save_news_data(news_data, json_file_path):
    """
    Saves the news data to a JSON file.
    
    Args:
        news_data (list): List of dictionaries containing news information.
        json_file_path (str): Path to the JSON file.
    """
    try:
        with open(json_file_path, 'w') as json_file:
            json.dump(news_data, json_file, indent=4)
    except IOError as e:
        print(f"Error saving JSON file: {e}")

def main():
    url = "https://www.himss.org/news"
    news_items = get_news_items(url)
    
    news_data = []
    for date, news_link in news_items:
        news_topic_text, content_text = extract_news_content(news_link)
        news_data.append({
            "news_url": news_link,
            "news_title": news_topic_text,
            "news_date": date.strftime('%Y-%m-%d:%H'),
            "news_content": content_text,
            "news_summary": "",
            "sentiment": "",
            "keywords_list": ""
        })
    
    temp_folder_path = os.path.join(os.getcwd(), "temp")
    if not os.path.exists(temp_folder_path):
        os.makedirs(temp_folder_path)
    
    json_file_path = os.path.join(temp_folder_path, "news_data.json")
    save_news_data(news_data, json_file_path)
    
    print(f"News data saved to {json_file_path}")

if __name__ == "__main__":
    main()