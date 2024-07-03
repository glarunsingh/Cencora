import logging
import sys

from langchain.chains import create_extraction_chain
from utils.load_model import model
from utils.logs import create_log

logger = create_log(name="Drug_Channel", level=logging.INFO)

schema_article_list = {
    "properties": {
        "news_article_title": {"type": "string"},
        "news_article_date": {"type": "string"},
        "news_article_url": {"type": "string"},
    },
    "required": ["news_article_title", "news_article_date", "news_article_url"],
}

schema_article_content = {
    "properties": {
        "news_article_content": {"type": "string"},
        "news_article_summary": {"type": "string"},
        "news_article_url": {"type": "string"},
    },
    "required": ["news_article_content", "news_article_summary", "news_article_url"],
}


async def extract_article_list_llm(html_content):
    extracted_article_list = create_extraction_chain(schema=schema_article_list, llm=model).invoke(html_content)
    article_list = extracted_article_list['text']
    print(article_list)
    for items in article_list:
        items['title'] = items.pop('news_article_title')
        items['date'] = items.pop('news_article_date')
        items['url'] = items.pop('news_article_url')
    logger.info("Extracted the article list and links using LLM")
    return article_list


async def extract_article_content_llm(html_content):
    try:
        raw_text= html_content.get_text(separator='')
        extracted_article_content = create_extraction_chain(schema=schema_article_content, llm=model).invoke(
            html_content)
        article_content = extracted_article_content['text'][0]
        logger.info("Extracted Content and Summarized using LLM")
        return article_content['news_article_content'], article_content['news_article_summary']
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return None, None
