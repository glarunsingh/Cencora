import logging
import sys
from typing import Literal, List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from DrugChannel.utils.llm_prompts import template, content_template, article_list_template
from DrugChannel.utils.load_model import model
from DrugChannel.utils.url_parameters import date_format
logger = logging.getLogger(__name__)

class response_schema(BaseModel):
    summary_schema: str = Field(description="Concise summary of the of the news article from the given context")
    sentiment_schema: Literal["Positive", "Negative", "Neutral"] = Field(
        description="Overall sentiment of the content whether it's Positive, Negative or Neutral")
    keyword_schema: List[str] = Field(
        description="Python List of matching keywords from the content based on a list of keywords provided.")


async def get_sum_key_sent(raw_text, url, key_list):
    """
    Asynchronously generates a summary, sentiment, and list of keywords from the given raw text and URL using the
    provided key list.

    Args:
        raw_text (str): The raw text to be summarized.
        url (str): The URL of the content.
        key_list (List[str]): The list of keywords to match against the content.

    Returns:
        Union[Dict[str, Any], None]: A dictionary containing the summary, sentiment, and list of keywords if successful.
                                      None if an error occurred.

    Raises:
        None

    Notes:
        - The function uses the `PydanticOutputParser` class to parse the output of the LLM model.
        - The `PromptTemplate` class is used to create a prompt template for the LLM model.
        - The `chain` object is created by piping the prompt, model, and parser together.
        - The `invoke` method is called on the `chain` object with the input variables and partial variables.
        - If an error occurs, an error message is logged and None is returned.
    """
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
    Asynchronously extracts a list of articles from the given raw text using the LLM scrapper.

    :param raw_text: The raw text containing the article list.
    :type raw_text: str
    :return: A list of dictionaries containing the URL, title, and date of each article.
    :rtype: List[Dict[str, Union[str, datetime]]]
    :raises Exception: If there is an error during the scraping process.
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
            f"Unable to scrape Drug channel Home page. - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
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
    Asynchronously generates and summarizes the content of an article using the LLM model.

    Args:
        raw_text (str): The raw text of the article.
        url (str): The URL of the article.
        key_list (List[str]): The list of keywords to match against the article content.

    Returns:
        Union[Dict[str, Any], None]: A dictionary containing the article content, summarization, sentiment, and list of
                                     keywords if successful.
                                      None if an error occurred.

    Raises:
        None

    Notes:
        - The function uses the `PydanticOutputParser` class to parse the output of the LLM model.
        - The `PromptTemplate` class is used to create a prompt template for the LLM model.
        - The `chain` object is created by piping the prompt, model, and parser together.
        - The `invoke` method is called on the `chain` object with the input variables and partial variables.
        - If an error occurs, an error message is logged and None is returned.
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
            f"Unable to generate and summarize using LLM.Hence Skipping! Url: {url} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
            stack_info=True)
        return None
