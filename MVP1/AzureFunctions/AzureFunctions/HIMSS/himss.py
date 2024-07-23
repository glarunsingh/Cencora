import logging
import time
import os
from dotenv import load_dotenv
import asyncio
import sys

from HIMSS.utils.logs import create_log
from HIMSS.utils.cosmos_function import HIMSSDBOPS
from HIMSS.utils.himss_data_extraction import get_himss_news_url_list, himss_extraction
from HIMSS.utils.summarizer import llm_content_sum_key_sent
import azure.functions as func

_ = load_dotenv('./HIMSS/config/db.env')

bp_himss = func.Blueprint()
logger = create_log(name="HIMSS", level=logging.INFO)
cron_time = os.getenv('HIMSS_CRON')
department = None

@bp_himss.timer_trigger(schedule=cron_time, arg_name="myTimer", run_on_startup=False,
                              use_monitor=False)
async def himss_scrapping_function(myTimer: func.TimerRequest):
    start_time = time.time()
    logger.info("Extracting information from HIMSS website")

    db_ops = HIMSSDBOPS()

    try:
        url = "https://www.himss.org/news"
        # Gets the Date and URL from the HIMSS News
        news_items_in_web = await get_himss_news_url_list(url)

        # Query the DB to get the 1st 10 URLs based on the data in the DB
        item_list_in_db = db_ops.query_and_sort_items_by_date(source_name='HIMSS', limit=16)

        # Create a set of URLs from item_list_in_db
        db_urls = set(url for _, url in item_list_in_db)

        # Find non-matching URLs
        non_matching_urls = []  # [url for _, url in news_items_in_web if url not in db_urls]

        for date, url in news_items_in_web:
            if url not in db_urls:
                non_matching_urls.append((date, url))

        # Print non-matching URLs
        print(f"Non-matching URLs:{len(non_matching_urls)}")
        logger.info(f"Non-matching URLs:{len(non_matching_urls)}")

        if len(non_matching_urls) > 0:
            for url in non_matching_urls:
                logger.info(f"Non-Matching URLs: {url}")
                print(url)

            extracted_data = await himss_extraction(non_matching_urls)

            # Extract data from HIMSS
            processed_data = []
            key_list = db_ops.query_keyword_list(department_name=department)

            for item in extracted_data:
                try:
                    # Process each item with LLM
                    llm_result = await llm_content_sum_key_sent(item['news_content'], item['news_url'], key_list)

                    processed_item = {
                        "news_url": item['news_url'],
                        "news_title": item['news_title'],
                        "news_date": item['news_date'],
                        "news_content": item['news_content'],
                        "news_summary": llm_result.summary_schema,
                        "sentiment": llm_result.sentiment_schema,
                        "keywords_list": llm_result.keyword_schema,
                        "source_name": "HIMSS"
                    }

                    processed_data.append(processed_item)
                    logger.info(f"Processed item: {item['news_url']}")
                except Exception as e:
                    logger.error(f"Error processing item {item['news_url']}: {str(e)}")

            # uploading the data in the cosmos db
            await db_ops.upsert_data(processed_data)

            # # Save processed data as JSON in temp folder
            # temp_folder = os.path.join(os.getcwd(), "temp")
            # os.makedirs(temp_folder, exist_ok=True)
            # json_file_path = os.path.join(temp_folder, f"himss_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            #
            # try:
            #     with open(json_file_path, 'w') as json_file:
            #         json.dump(processed_data, json_file, indent=4)
            #     logger.info(f"Processed data saved to {json_file_path}")
            # except IOError as e:
            #     logger.error(f"Error saving JSON file: {str(e)}")

            end_time = time.time()
            logger.info(f"Total execution time: {end_time - start_time} seconds")

            return processed_data
        else:
            logger.info("No new news items found")
            return None

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Unhandled Exception: Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)

# Run the main function using asyncio
# if __name__ == "__main__":
#     # Define an asynchronous function to call the scrapping function
#     async def main():
#         await himss_scrapping_function()
#     asyncio.run(main())
