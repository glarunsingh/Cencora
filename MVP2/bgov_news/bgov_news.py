import logging
import time
import asyncio
import json


from utils.logs import create_log
from utils.bgov_news_scraping import bgov_news_main_page_scraping
from utils.summarizer import llm_content_sum_key_sent
from utils.cosmos_function import DBOPS

logger = create_log(name="bgov", level=logging.INFO)
department = None
start_time = time.time()
logger.info(f"bgov_news program starts...")

async def bgov_news():

        # URL of the page to scrape
        url = "https://about.bgov.com/news/"

        db_ops = DBOPS()

        key_list = db_ops.query_keyword_list(department_name=department)

        processed_data = []
        # Call the function from the extractor module
        news_items = bgov_news_main_page_scraping(url)
        print(news_items)d

        for item in news_items:
                try:    
                        #print(item)
                        llm_result = await llm_content_sum_key_sent(item['content'], item['url'], key_list)
                        #print(llm_result.summary_schema)
                        processed_item = {
                                'news_url': item['url'],
                                'news_title': item['title'],
                                'news_date': item['date'],
                                'news_content': item['content'],
                                #'news_brief_content': item['brief_content'],
                                'news_summary': llm_result.summary_schema,
                                'news_sentiment': llm_result.sentiment_schema,
                                'news_keywords': llm_result.keyword_schema,
                                'source_name': "bgov",
                                'client_name': ""
                        }
                        processed_data.append(processed_item)
                except Exception as e:
                        logger.error(f"Error processing item {item['url']}: {str(e)}")
        
        # Define the filename
        filename = 'organized_news.json'
        
        for item in processed_data:
                logger.info(f"Processed item: {item}")
        
        # Write the collection to a JSON file
        with open(filename, 'w') as json_file:
                json.dump(processed_data, json_file, indent=4)

        print(f"News items have been written to {filename}.")

        logger.info(f"Total time taken: {time.time() - start_time}")
        logger.info(f"bgov_news program ends...")

# Define an asynchronous function to call the scrapping function
async def main():
    await bgov_news()

# Run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())
