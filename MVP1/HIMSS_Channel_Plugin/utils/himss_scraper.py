import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_news_items(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    news_items = []

    exclude_urls = {
        "https://www.himss.org/news/mobihealthnews",
        "https://www.himss.org/news/michigan-healthcare-it-news",
        "https://www.himss.org/news/healthcare-finance-news",
        "https://www.himss.org/news/himss-tv"
    }
    
    #Replace with actual parsing logic
    for article in soup.find_all('div', class_='mb-5 grid-12 card-list views-row'):
        date_div = article.find('div', class_='date')
        url_div = article.find('a', href=True)
        
        if date_div and url_div:
            date_text = date_div.get_text(strip=True)
            try:
                article_date = datetime.strptime(date_text, '%B %d, %Y')
                datetime
            except ValueError as e:
                print(f"Error parsing date: {e}")
                continue
            href = url_div['href']
            
            full_url = f"https://www.himss.org{href}"
            if full_url not in exclude_urls:
                news_items.append((article_date, full_url))
    
    news_items.sort(key=lambda x: x[0], reverse=True)
    return news_items

        #date = datetime.datetime.strptime(item.select_one('.date').text, '%Y-%m-%d')
        #news_link = item.select_one('a')['href']
        #news_items.append((date,news_link))

    #return news_items

def extract_news_content(news_link):
    response = requests.get(news_link)
    news_soup = BeautifulSoup(response.content, 'html.parser')

    news_topic = news_soup.find('h1', class_='white')
    news_topic_text = news_topic.get_text(strip=True) if news_topic else "No title found"

    content_div = news_soup.find('div', class_='field-body')
    content_text = content_div.get_text(strip=True, separator=' ') if content_div else "No content found"

    return news_topic_text, content_text