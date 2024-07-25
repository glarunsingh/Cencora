import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime

from utils.logs import create_log

logger = create_log(name="HIMSS", level=logging.INFO)

def bgov_news_main_page_scraping(url):

    # List to hold news items
    news_items = []

    # Send a GET request to the page
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Print the HTML content to verify it
    #print(soup.prettify())

    # Find the main content div
    content_div = soup.find('div', id='content', class_='bgov-content ft-fluid')

    # Find all teaser divs within the main content div
    teaser_divs = content_div.find_all('div', class_='teaser news ft-container')

    # Loop through each teaser div to extract the information
    for teaser in teaser_divs:
        # Extract the URL
        url = teaser.find('a')['href']
        
        # Extract the title
        title = teaser.find('h3').get_text(strip=True)
        
        # Extract the posted datetime
        datetime = teaser.find('time')['datetime']
        
        # Extract the content
        content = ' '.join(teaser.find('div', class_='entry-excerpt').stripped_strings)
        brief_content = scrap_news_content_in_url(url)

        # Append to the list as a dictionary
        news_items.append({
            'url': url,
            'title': title,
            'datetime': datetime,
            'content': content,
            'brief_content': brief_content,
        })

    return news_items

def scrap_news_content_in_url(url):

    # Send a GET request to the page
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    content_div = soup.find('div', class_='news__content ft-col-lg8 ft-col-sm12')
    if not content_div:
        print(f"Error: No content found at {url}")
        return
    # Extract text from the content_div
    brief_content = ''
    for section in content_div.find_all(['p', 'ul', 'h3', 'figure']):
        if section.name == 'figure':
            img = section.find('img')
            if img and img.get('src'):
                brief_content += f"Image URL: {img['src']}\n"
            caption = section.find('div', class_='news-figure-caption-text')
            if caption:
                brief_content += f"Caption: {caption.get_text(strip=True)}\n"
        else:
            brief_content += f"{section.get_text(separator=' ', strip=True)}\n\n"

    return brief_content