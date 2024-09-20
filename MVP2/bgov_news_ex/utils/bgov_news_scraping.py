import requests
import json
import logging
import re

from bs4 import BeautifulSoup
from datetime import datetime
from utils.logs import create_log

logger = create_log(name="HIMSS", level=logging.INFO)
urls = []
unique_urls = []

def bgov_news_main_page_scraping(url):
    # List to hold news items
    news_items = []

    # Send a GET request to the page
    response = requests.get(url)
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all teaser news containers
        teaser_divs = soup.find_all('div', class_='teaser news ft-container')
        
        # Extract URLs
        for teaser in teaser_divs:
            # Find the <a> tags within each teaser
            a_tags = teaser.find_all('a', href=True)
            for a in a_tags:
                # Append the href attribute to the list of URLs
                urls.append(a['href'])
        
        # Print or use the list of URLs
        #print(urls)
        #unique_urls = list(set(urls))
        #print(f"Unique urls: {unique_urls}")
    else:
        print(f"Failed to retrieve content, status code: {response.status_code}")

    # Remove duplicate URLs
    unique_urls = list(set(urls))
    print(unique_urls)

    # List to store the extracted content
    articles = []

    # Process each unique URL
    for url in unique_urls:
        html_content = fetch_html(url)
        article_content = extract_content(html_content)
        if article_content:
            articles.append({
                'url': url,
                **article_content
            })

    # Write the content to a JSON file
    with open('extracted_articles.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
        
    return articles

def fetch_html(url):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.content
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    
# Function to extract content from HTML
def extract_content(html):
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # Extract the title
    title_tag = soup.find('h1', class_='news__header__title')
    title = title_tag.get_text(strip=True) if title_tag else 'No title found'

    # Extract the date
    time_tag = soup.find('time')
    date = time_tag.get_text(strip=True) if time_tag else 'No date found'

    # Extract the article body
    content_div = soup.find('div', class_='news__content')
    paragraphs = content_div.find_all('p') if content_div else []
    content = '\n'.join(p.get_text(strip=True) for p in paragraphs)

    return {
        'title': title,
        'date': date,
        'content': content
    }