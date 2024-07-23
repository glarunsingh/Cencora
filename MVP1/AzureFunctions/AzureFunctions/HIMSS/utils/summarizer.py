import logging
import sys
from typing import Literal, List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from HIMSS.utils.llm_prompts import template, content_template, article_list_template
from HIMSS.utils.load_model import model
from HIMSS.utils.logs import create_log
from HIMSS.utils.url_parameters import date_format

logger = create_log(name="HIMSS", level=logging.INFO)


class response_schema(BaseModel):
    summary_schema: str = Field(description="Concise summary of the of the news article from the given context")
    sentiment_schema: Literal["positive", "negative", "neutral"] = Field(
        description="Overall sentiment of the content whether it's positive, negative or neutral")
    keyword_schema: List[str] = Field(
        description="Python List of matching keywords from the content based on a list of keywords provided.")


async def get_sum_key_sent(raw_text, url, key_list):
    try:
        parser = PydanticOutputParser(pydantic_object=response_schema)
        prompt = PromptTemplate(
            template=template,
            input_variables=["content", "keywords_list"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt | model | parser
        out = chain.invoke({"content": raw_text, "keywords_list": key_list})
        logger.info("Summarization, Sentiment and Keywords Extraction Complete")
        return out

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(
            f"Unable to summarize content.Hence Skipping! Url: {url} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
            stack_info=True)
        return None


class LLM_articles_details(BaseModel):
    url: str = Field(description="Url of the article")
    title: str = Field(description="Title of the article")
    date: str = Field(description="Date of the article")


class articles_list(BaseModel):
    properties: List[LLM_articles_details]


async def llm_article_list(raw_text):
    """
    Function to extract url,title,date for the articles.When LLM Scrapper is set to true.
    :param raw_text:
    :return:
    """
    try:
        parser = PydanticOutputParser(pydantic_object=articles_list)
        prompt = PromptTemplate(
            template=article_list_template,
            input_variables=["raw_content"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt | model | parser
        extracted_article_list = chain.invoke({"raw_content": raw_text})
        # print("efdefe", extracted_article_list)
        article_properties = extracted_article_list.properties
        article_list = []
        for item in article_properties:
            temp = {'url': item.url, 'title': item.title, 'date': date_format(item.date)}
            article_list.append(temp)

        logger.info("Extracted the article list and links using LLM")
        return article_list

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(
            f"Unable to scrape HIMSS channel Home page. - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
            stack_info=True)
        raise Exception


class Llm_Content_Schema(BaseModel):
    content_schema: str = Field(description="Article content from the website raw content provided")
    summary_schema: str = Field(description="Concise summary of the of the news article from the article scrapped")
    sentiment_schema: Literal["Positive", "Negative", "Neutral"] = Field(
        description="Overall sentiment of the article content whether it's Positive, Negative or Neutral")
    keyword_schema: List[str] = Field(
        description="Python List of matching keywords from the article content based on a list of keywords provided.")


async def llm_content_sum_key_sent(raw_text, url, key_list):
    """
    Function to extract content,summary,sentiment and keywords from the website.When LLM Scrapper is set to true.
    :param raw_text:
    :param url:
    :param key_list:
    :return:
    """
    try:
        parser = PydanticOutputParser(pydantic_object=Llm_Content_Schema)
        prompt = PromptTemplate(
            template=content_template,
            input_variables=["raw_content", "keywords_list"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | model | parser
        out = chain.invoke({"raw_content": raw_text, "keywords_list": key_list})
        logger.info("Article Content, Summarization, Sentiment and Keywords Extraction Complete")
        return out

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(
            f"Unable to generate and summarize using LLM.Hence Skipping! Url: {url} - Line No: {exc_tb.tb_lineno}"
            f"  Error: {str(e)}",stack_info=True)
        return None
