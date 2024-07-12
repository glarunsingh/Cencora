import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from utils.logs import create_log
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
        response = requests.get(url, headers=url_headers(), timeout=read_timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching the URL: {url}. Error: {str(e)}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    exclude_urls = {
        "https://www.himss.org/news/mobihealthnews",
        "https://www.himss.org/news/michigan-healthcare-it-news",
        "https://www.himss.org/news/healthcare-finance-news",
        "https://www.himss.org/news/himss-tv"
    }
    
    news_items = []
    for article in soup.find_all('div', class_='mb-5 grid-12 card-list views-row'):
        try:
            date_div = article.find('div', class_='date')
            url_div = article.find('a', href=True)
            
            if date_div and url_div:
                date_text = date_div.get_text(strip=True)
                article_date = datetime.strptime(date_text, '%B %d, %Y')
                href = url_div['href']
                
                full_url = f"https://www.himss.org{href}"
                if full_url not in exclude_urls:
                    news_items.append((article_date, full_url))
        except Exception as e:
            logger.error(f"Error processing article: {str(e)}")
    
    news_items.sort(key=lambda x: x[0], reverse=True)
    logger.info(f"Found {len(news_items)} news items")
    return news_items

async def extract_news_content(news_link):
    """
    Extracts the main content of a news article from the given URL.
    
    Args:
        news_link (str): URL of the news article.
    
    Returns:
        tuple: (news_topic_text, content_text)
    """
    try:
        news_response = requests.get(news_link, headers=url_headers(), timeout=read_timeout)
        news_response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching the news article: {news_link}. Error: {str(e)}")
        return None, None

    news_soup = BeautifulSoup(news_response.content, 'html.parser')
    
    news_topic = news_soup.find('h1', class_='white')
    news_topic_text = news_topic.get_text(strip=True) if news_topic else "No title found"
    
    content_div = news_soup.find('div', class_='field-body')
    content_text = content_div.get_text(strip=True, separator=' ') if content_div else "No content found"
    
    logger.info(f"Extracted content from: {news_link}")
    return news_topic_text, content_text

async def himss_extraction():
    """
    Main function to extract news data from HIMSS website.
    
    Returns:
        list: List of dictionaries containing extracted news data.
    """
    url = "https://www.himss.org/news"
    try:
        news_items = await get_news_items(url)
        
        news_data = []
        for date, news_link in news_items:
            try:
                news_topic_text, content_text = await extract_news_content(news_link)
                
                if news_topic_text and content_text:
                    news_item = {
                        "news_url": news_link,
                        "news_title": news_topic_text,
                        "news_date": date.strftime('%Y-%m-%d:%H'),
                        "news_content": content_text,
                    }
                    
                    news_data.append(news_item)
                    logger.info(f"Extracted item: {news_link}")
                else:
                    logger.warning(f"Skipped item due to missing content: {news_link}")
            except Exception as e:
                logger.error(f"Error processing news item {news_link}: {str(e)}")

        logger.info(f"Extracted {len(news_data)} items from HIMSS")
        return news_data

    except Exception as e:
        logger.error(f"Error in HIMSS extraction process: {str(e)}")
        return []

if __name__ == "__main__":
    # This block allows you to run this script independently for testing
    import asyncio
    
    async def main():
        extracted_data = await himss_extraction()
        print(f"Extracted {len(extracted_data)} items")

    asyncio.run(main())