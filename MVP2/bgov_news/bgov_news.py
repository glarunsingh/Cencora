import logging
import time

from utils.logs import create_log
from utils.bgov_news_scraping import bgov_news_main_page_scraping


logger = create_log(name="bgov", level=logging.INFO)

start_time = time.time()
logger.info(f"bgov_news program starts...")

# URL of the page to scrape
url = "https://about.bgov.com/news/"

# Call the function from the extractor module
news_items = bgov_news_main_page_scraping(url)
for item in news_items:
        logger.info(item)

logger.info(f"bgov_news program ends...")

