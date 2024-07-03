import logging
import re
import sys

import requests
from bs4 import BeautifulSoup

from utils import logs
from utils.llm_scrapper import extract_article_content_llm
from utils.logs import create_log
from utils.summarizer import get_summary
from utils.url_parameters import url_headers, read_timeout

logger = create_log(name="Drug_Channel", level=logging.INFO)


async def extract_content_dc(url,date, headers=url_headers(),use_llm=False):
    try:
        response = requests.get(url,headers=headers,timeout=read_timeout)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # print(soup)
            if use_llm:
                content,summary= await extract_article_content_llm(soup)
            else:
                data = soup.find('div', {'class': 'post hentry'})

                # Remove the post-title
                for div in data.find_all("h3", {'class': 'post-title entry-title'}):
                    div.decompose()

                # Remove the post footer
                class_name = 'post-footer'
                for div in data.find_all("div", {'class': 'post-footer'}):
                    div.decompose()
                raw_text = data.get_text(separator='')

                # Remove "[Click to Enlarge]" text from the text
                content = raw_text.replace("[Click to Enlarge]", "")

                # Remove the first and last space of string
                content = content.strip()

                # Remove unnecessary space in between lines
                content = re.sub(r'(\n){3,}', '\n\n', content)
                logger.info(f"Extracted Content")

                # Getting summary
                summary = await get_summary(content, date=date, url=url)

            return content,summary
        else:
            logger.warning(f"Url not responding.Hence skipping! Url: {url} Request status code: {response.status_code}")
            return None,None



    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Unable to fetch data Url: {url} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return None,None

