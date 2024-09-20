"""
Main application for Bing News Web Tools Plugin
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
import sys
from urllib.parse import urlparse

# FastAPI imports
from fastapi import APIRouter

from BingNews_Plugin.utils import crawler
from BingNews_Plugin.utils import scrapper
from BingNews_Plugin.utils import summarizer

import logging
logger = logging.getLogger(__name__)

#logger = logger.create_log(name="BingNews_Plugins", level=logging.INFO)
#logger = logger.create_log(level=logging.INFO)
router = APIRouter(prefix='/bing_news_plugin', tags=['bing_news_plugin'])

class input_schema(BaseModel):
    searchType: Optional[Literal["News", "Search"]] = Field(default="Search",
                                                            description="Result searchType News or Search")
    maxResults: Optional[int] = Field(default=5, description="Number of max results to return")
    scrape: Optional[bool] = Field(default=False, description="whether results url should be scraped to get full page")
    summarize: Optional[bool] = Field(default=False,
                                      description="whether results full page should be summarized, only when scrape "
                                                  "parameter is true")
    summaryPrompt: Optional[str] = Field(default="",
                                         description="If scrape is true and summarize = true and has text, use prompt "
                                                     "for summarization")
    searchTerm: str = Field(description="text to be searched")
    location: Optional[Literal["US"]] = Field(default="US",
                                              description="country codes for specific location https://learn.microsoft."
                                                          "com/en-us/bing/search-apis/bing-web-search/reference/"
                                                          "market-codes")
    minDate: str = Field(default="YYYY-MM-DD", description="Minimum date from when to get results format = YYYY-MM-DD")


@router.post("/GetBingResults")
async def get_bing_results(input: input_schema):
    """
    Endpoint to extract Bing news using API, get content using request calls and summarize the news article
    params:
        searchType: (enum of News/Search) (Default: Search if not supplied) - OPTIONAL
        maxResults:(number of max results to return) (Default: 5 if not supplied) - OPTIONAL
        scrape:(bool whether results url should be scraped to get full page) (Default: false if not supplied) - OPTIONAL
        summarize:(bool only when scrape is true, summarize the scraped data) (Default: false if not supplied)
        - OPTIONAL
        summaryPrompt:If scrape is true and summarize = true and has text, use prompt for summarization - Default Empty
        - OPTIONAL
        searchTerm:(text to be searched) - REQUIRED
        location: (get results only for specific location) (Default: United States of America if not supplied)
        - OPTIONAL
        minDate: Minimum date from when to get results (Default: none if not supplied) - OPTIONAL
    returns:
        Gets a JSON Array of results with properties
        title, url, date, content (will be snippet/fullpage/summary if specified)
    """
    try:
        searchType = input.searchType
        maxResults = input.maxResults
        scrape = input.scrape
        summarize = input.summarize
        summaryPrompt = input.summaryPrompt
        searchTerm = input.searchTerm
        location = input.location
        minDate = input.minDate

        if searchType == "News":
            data = crawler.bing_news_crawler(search_term=searchTerm, location=location)
        else:
            data = crawler.bing_search_crawler(search_term=searchTerm, location=location)
        logger.info(f"Bing data extracted successfully for {searchTerm}: #of News {len(data)} for month")
        logger.info(f"Now Filtering of news will be started according to date and max results")
        if len(data) > 0:
            # Extract the date values and convert them to datetime objects
            date_values = [d["date"] for d in data]
            result_data = []
            if minDate is not None:
                for item in data:
                    try:
                        if datetime.strptime(item['date'].split("T")[0], "%Y-%m-%d").date()>= datetime.strptime(minDate, "%Y-%m-%d").date():
                        #if item['date'].split("T")[0]>= minDate:
                            result_data.append(item)
                    except:
                        logger.info(f"Filtering of news according to date is failed as either minDate {minDate} or news date is invalid {item['date']}")
                        result_data.append(item)
                logger.info(f"After filtering according to date {minDate} # of News {len(result_data)}")
            else:
                logger.info(f"Filtering of news according to date is failed as date is invalid :{minDate}")
                result_data=data
                
            if len(result_data) > maxResults:
                result_data = result_data[:maxResults]
            logger.info(f"After filtering according to maxResults: {maxResults} # of News {len(result_data)}")
            if scrape and len(result_data)>0:
                logger.info(f"Starting all the News Scrapping")
                result_data= scrapper.all_scrapper(result_data)
                logger.info(f"Completed all the News Scrapping")
                if scrape and summarize:
                    logger.info(f"Starting all the News Summarization")
                    if len(summaryPrompt)>1:
                        summary_object= summarizer.news_summarizer(summary_prompt = summaryPrompt)
                        if summary_object.connection_error==False:
                            summary_object.summarize(news_data=result_data)
                            result_data= summary_object.output
                        else:
                            logger.info(f"Not Able to connect with Azure Open AI")
                    else:
                        logger.info(f"Not summarizing the news as summary prompt is empty")
                    logger.info(f"Completed all the News Summarization")
            else:
                logger.info(f"Latest Bing News available for {searchTerm}: is on {max(date_values)}")
                #print(f"Latest Bing News available for {searchTerm}: is on {max(date_values)}")
                return {'success': True,
                        'message': f"Latest Bing News available for {searchTerm}: is on {max(date_values)}",
                        "data": result_data}
        else:
            logger.info(f"No Bing news available for {searchTerm}: #of News {len(data)}")
            print(f"Bing news not available for {searchTerm}: #of News {len(data)}")
            return {'success': True, 'message': f"Bing news not available for {searchTerm}", "data": result_data}
        # print(result_data)
        logger.info(f"Bing data extracted successfully for {searchTerm}: #of News {len(result_data)}")
        return {'success': True, 'message': "Bing data extraction Success", "data": result_data}
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.info(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return ({'success': False, 'message': "Bing data extraction failed",
                 "data": []})


@router.post("/GetBingResultsText")
async def get_bing_results_text(input: input_schema):
    """
    Endpoint to extract Bing news using API, get content using request calls and summarize the news article
    params:
        searchType: (enum of News/Search) (Default: Search if not supplied) - OPTIONAL
        maxResults:(number of max results to return) (Default: 5 if not supplied) - OPTIONAL
        scrape:(bool whether results url should be scraped to get full page) (Default: false if not supplied) - OPTIONAL
        summarize:(bool only when scrape is true, summarize the scraped data) (Default: false if not supplied) - OPTIONAL
        summaryPrompt:If scrape is true and summarize = true and has text, use prompt for summarization - Default Empty
        - OPTIONAL
        searchTerm:(text to be searched) - REQUIRED
        location: (get results only for specific location) (Default: United States of America if not supplied)
        - OPTIONAL
        minDate: Minimum date from when to get results (Default: none if not supplied) - OPTIONAL
    returns:
        Gets the below text
        RESULTS

        RESULT 1
        TITLE: <title>
        URL: <url>
        DATE: <date>
        CONTENT: <snippet/scrape/summary>
        END RESULT 1
    """
    try:
        searchType = input.searchType
        maxResults = input.maxResults
        scrape = input.scrape
        summarize = input.summarize
        summaryPrompt = input.summaryPrompt
        searchTerm = input.searchTerm
        location = input.location
        minDate = input.minDate

        if searchType == "News":
            data = crawler.bing_news_crawler(search_term=searchTerm, location=location)
        else:
            data = crawler.bing_search_crawler(search_term=searchTerm, location=location)
        logger.info(f"Bing data extracted successfully for {searchTerm}: #of News {len(data)} for month")
        logger.info(f"Now Filtering of news will be started according to date and max results")
        if len(data) > 0:
            # Extract the date values and convert them to datetime objects
            date_values = [d["date"] for d in data]

            result_data = []
            if minDate is not None:
                for item in data:
                    try:
                        if datetime.strptime(item['date'].split("T")[0], "%Y-%m-%d").date()>= datetime.strptime(minDate, "%Y-%m-%d").date():
                        #if item['date'].split("T")[0]>= minDate:
                            result_data.append(item)
                    except:
                        logger.info(f"Filtering of news according to date is failed as either minDate {minDate} or news date is invalid {item['date']}")
                        result_data.append(item)
                logger.info(f"After filtering according to date {minDate} # of News {len(result_data)}")
            else:
                logger.info(f"Filtering of news according to date is failed as date is invalid :{minDate}")
                result_data=data
                
            if len(result_data) > maxResults:
                result_data = result_data[:maxResults]
            logger.info(f"After filtering according to maxResults: {maxResults} # of News {len(result_data)}")
            if len(result_data) > 0:
                if scrape:
                    logger.info(f"Starting all the News Summarization")
                    result_data= scrapper.all_scrapper(result_data) 
                    logger.info(f"Completed all the News Scrapping")
                if scrape and summarize:
                    logger.info(f"Starting all the News Summarization")
                    if len(summaryPrompt)>1:
                        summary_object= summarizer.news_summarizer(summary_prompt = summaryPrompt)
                        if summary_object.connection_error==False:
                            summary_object.summarize(news_data=result_data)
                            result_data= summary_object.output
                        else:
                            logger.info(f"Not Able to connect with Azure Open AI")
                    else:
                        logger.info(f"Not summarizing the news as summary prompt is empty")
            else:
                logger.info(f"Latest Bing News available for {searchTerm}: is on {max(date_values)}")
                print(f"Latest Bing News available for {searchTerm}: is on {max(date_values)}")
                return {'success': True,
                        'message': f"Latest Bing News available for {searchTerm}: is on {max(date_values)}",
                        "data": result_data}
        else:
            logger.info(f"No Bing news available for {searchTerm}: #of News {len(data)}")
            print(f"Bing news not available for {searchTerm}: #of News {len(data)}")
            return {'success': True, 'message': f"Bing news not available for {searchTerm}", "data": result_data}

        # Initialize an empty result string
        result_string = "RESULTS \n\n"

        # Process each item in the data
        for i, item in enumerate(result_data, start=1):
            result_string += f"RESULT {i}\n"
            result_string += f"TITLE: {item['title']}\n"
            result_string += f"URL: {item['url']}\n"
            result_string += f"DATE: {item['date']}\n"
            result_string += f"CONTENT: {item['content']}...\n"
            result_string += f"END RESULT {i}\n\n"

        logger.info(f"Bing data extracted successfully for {searchTerm}: {len(data)}")
        return {'success': True, 'message': "Bing data extraction Success", "data": result_string}
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.info(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return ({'success': False, 'message': "Bing data extraction failed",
                "data": []})


class scrape_schema(BaseModel):
    url: str = Field(description="The url to be scraped")
    summarize: Optional[bool] = Field(default=False,
                                      description="whether results full page should be summarized, only when scrape "
                                                  "parameter is true")
    summaryPrompt: Optional[str] = Field(default="",
                                         description="If summarize = true and has text, use prompt for summarization")


@router.post("/ScrapeURL")
async def scrape_url(input: scrape_schema):
    """
    Endpoint to scrape the given url and summarize the news article if required
    params:
        url:  (the url to be scraped) - REQUIRED
        summarize:(bool summarize the scraped data) (Default: false if not supplied) - OPTIONAL
        summaryPrompt:If summarize = true and has text, use prompt for summarization - Default Empty - OPTIONAL
    returns:
    ScrapeURL A json object with the following properties
        url: The Input URL
        status: boolean specifying if scrape+summarization succeeded or failed
        content: the content (or summary) of the page text
    """
    try:
        url = input.url
        summarize = input.summarize
        summaryPrompt = input.summaryPrompt

        article_content = scrapper.news_scrapper(url)
        result_data = {"url": url, "status": "Fail", "content": article_content}
        if article_content is not None:
            result_data["status"] = "Pass"
            if summarize:
                summary_content=None
                if len(summaryPrompt)>1:
                    summary_object= summarizer.news_summarizer(summaryPrompt)
                    summary_content = summary_object.generate_summary(article_content)
                else:
                    logger.info(f"Not summarizing the news as summary prompt is empty")
                                
                if summary_content is not None:
                    result_data["content"] = summary_object.generate_summary(article_content)
                else:
                    result_data["status"]="Fail" 

        logger.info(f"Given url processed successfully {url}")
        return {'success': True, 'message': "Given url processed successfully", "data": result_data}
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.info(f"failed to process given url {url} Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return ({'success': False, 'message': "failed to process given url",
                 "data": []})


@router.post("/ScrapeURLText")
async def scrape_url_text(input: scrape_schema):
    """
    Endpoint to scrape the given url and summarize the news article if required
    params:
        url:  (the url to be scraped) - REQUIRED
        summarize:(bool only when scrape is true, summarize the scraped data) (Default: false if not supplied)
        - OPTIONAL
        summaryPrompt:If summarize = true and has text, use prompt for summarization - Default Empty - OPTIONAL
    returns:
    A text object with the following
        SOURCE NAME: <name>
        SOURCE URL: <url>
        CONTENT:
        <text>
    """
    try:
        url = input.url
        summarize = input.summarize
        summaryPrompt = input.summaryPrompt

        article_content = scrapper.news_scrapper(url)
        if article_content is not None:
            if summarize:
                summary_content=None
                if len(summaryPrompt)>1:
                    summary_object= summarizer.news_summarizer(summaryPrompt)
                    summary_content = summary_object.generate_summary(article_content)
                else:
                    logger.info(f"Not summarizing the news as summary prompt is empty")
                
                if summary_content is not None:
                    article_content= summary_content

        source_name = urlparse(url).hostname

        result_string = f"SOURCE NAME: {source_name}\n"
        result_string += f"SOURCE URL: {url}\n"
        result_string += f"CONTENT:\n"
        result_string += f"{article_content}\n"

        logger.info(f"The given url is processed successfully {url}")
        return {'success': True, 'message': "Given url processed successfully", "data": result_string}
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.info(f"failed to process given url {url} Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return ({'success': False, 'message': "failed to process given url",
                 "data": []})
