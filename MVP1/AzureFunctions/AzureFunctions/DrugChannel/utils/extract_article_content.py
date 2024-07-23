import logging
import re
import sys

import requests
from bs4 import BeautifulSoup

from DrugChannel.utils.logs import create_log
from DrugChannel.utils.summarizer import get_sum_key_sent, llm_content_sum_key_sent
from DrugChannel.utils.url_parameters import url_headers, read_timeout

logger = create_log(name="Drug_Channel", level=logging.INFO)


async def extract_content_dc(url, date, headers=url_headers(), use_llm=False, key_list=[]):
    """
    Extracts content from a given URL, processes it including removing unnecessary content,
    and retrieves a summary of the content.

    Parameters:
        url (str): The URL from which to extract the content.
        date: The date associated with the content.
        headers: The headers to use for the request. Defaults to the headers returned by url_headers().
        use_llm (bool): A flag indicating whether to use the LLM scrapper. Defaults to False.
        key_list (list): A list of keywords to use for content extraction.

    Returns:
        tuple: A tuple containing the extracted content and summary information.
            content (str): The extracted content from the URL.
            sum_key_sent: Summary information including sentiment and keywords.
    """
    try:
        response = requests.get(url, headers=headers, timeout=read_timeout)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            if use_llm:
                raw_text = soup.get_text(separator='')
                sum_key_sent = await llm_content_sum_key_sent(raw_text, url=url, key_list=key_list)
                content = sum_key_sent.content_schema
            else:
                data = soup.find('div', {'class': 'post hentry'})

                # Remove the post-title
                for div in data.find_all("h3", {'class': 'post-title entry-title'}):
                    div.decompose()

                # Remove the post footer
                for div in data.find_all("div", {'class': 'post-footer'}):
                    div.decompose()
                # Remove the p tag i.e. drug channel advertisement
                for div in data.find_all('p'):
                    div.decompose()

                raw_text = data.get_text(separator='')

                # Remove "[Click to Enlarge]" text from the text
                content = raw_text.replace("[Click to Enlarge]", "")

                # Remove the first and last space of string
                content = content.strip()

                # Remove unnecessary space in between lines
                content = re.sub(r'(\n){3,}', '\n\n', content)
                logger.info(f"Extracted Content")

                # Getting summary,keywordssentiment
                sum_key_sent = await get_sum_key_sent(content, url=url, key_list=key_list)

            return content, sum_key_sent
        else:
            logger.warning(f"Url not responding.Hence skipping! Url: {url} Request status code: {response.status_code}")
            return None, None

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Unable to fetch data Url: {url} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return None, None
