import logging
import sys
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from DrugChannel.utils.summarizer import llm_article_list
from DrugChannel.utils.url_parameters import url_headers, read_timeout, dateformat

logger = logging.getLogger(__name__)

async def get_articles_list_dc(year: int, month: int, headers=url_headers(), use_llm=False):
    """
    Asynchronously retrieves a list of articles from Drug Channels for a specific year and month.

    Parameters:
        year (int): The year for which the articles are to be retrieved.
        month (int): The month for which the articles are to be retrieved.
        headers (dict, optional): The headers to be included in the request (default is url_headers()).
        use_llm (bool, optional): Flag to indicate whether to use the llm scrapper for article extraction.
                                  Default is False.

    Returns:
        list: A list of dictionaries containing the URL, title, and date of each article.
    """
    non_empty_articles = []
    try:
        month_str = f"{month:02}"
        year_str = f"{year:04}"

        url = f"https://www.drugchannels.net/{year_str}/{month_str}"
        logger.info(f"Extracting list from {url}")
        # Send a GET request to Drug Channels
        response = requests.get(url, headers=headers, timeout=read_timeout)
        if response.status_code == 200:
            # Parse the page with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            # Initialize an empty list to store the dictionaries
            articles_info = []

            # If you use_llm is True, extract the article list using the llm scrapper
            if use_llm:
                non_empty_articles = await llm_article_list(soup)

            else:
                # Find all articles
                articles = soup.find_all("div", attrs={"class": "date-outer"})

                # Loop through all articles
                for article in articles:
                    # Find the time element (replace 'time' with the actual tag name)
                    # time_element = article.find("h2", class_="date-header")
                    time_element = article.find("abbr", attrs={"class": "published"}).get("title")

                    if time_element:
                        # Get the datetime attribute
                        datetime_str = datetime.fromisoformat(time_element)
                        # Parse the datetime string
                        utc_datetime = datetime_str.astimezone(timezone.utc)

                        # Format the datetime object
                        date_str = utc_datetime.strftime(dateformat)

                        # Extract post-information
                        post_info = article.find("h3", class_="post-title entry-title")

                        # Get the href attribute
                        article_link = post_info.find("a").get("href")

                        # Get the link text
                        article_text = post_info.text.strip()

                        # Create a dictionary with the href, title, and date
                        article_dict = {
                            "url": article_link,
                            "title": article_text,
                            "date": date_str
                        }
                        articles_info.append(article_dict)

                # Now check if 'date' key exists in each dictionary before trying to access it
                articles_info = [article for article in articles_info if 'date' in article]

                # Now convert the date strings back to datetime objects, sort the list, and convert them back to strings
                articles_info = sorted((dict(t, date=datetime.strptime(t['date'], dateformat)) for t in articles_info),
                                       key=lambda x: x['date'], reverse=True
                                       )
                for article_info in articles_info:
                    article_info['date'] = article_info['date'].strftime(dateformat)

                # Create a new list that includes only the dictionaries with a non-empty title
                non_empty_articles = [article for article in articles_info if article['title'].strip()]

                logger.info("Extracted the article list and links")
            return non_empty_articles

        else:
            logger.error(f"Unable to fetch data from {url} Request status code: {response.status_code}",
                         stack_info=True)
            raise Exception

    except Exception as e:
        # failure_cnt = failure_cnt + 1
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        raise Exception
