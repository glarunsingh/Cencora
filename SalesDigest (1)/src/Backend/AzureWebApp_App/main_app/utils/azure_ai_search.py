import logging
import os
import sys
import time


import markdown2
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers.structured import ResponseSchema,StructuredOutputParser
from config.key_vault import key_vault
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import Literal, List

secret_value = key_vault()
logger = logging.getLogger(__name__)
from config.load_model import embeddings,model

#from main_app.utils.keyword_prompt import consolidated_summary_template
#from main_app.utils.keyword_prompt import insights_summary_template
#from main_app.utils.keyword_prompt import report_summary_template
from main_app.utils.helper import helper
from feedback_page.utils.db_helper import DBOPS
from main_app.utils.digest_db import ConfigDBOPS

feedback_db = DBOPS()
helper = helper()

config_db= ConfigDBOPS()

class Azure_AI_Search:
    """
    Class to perform Azure AI Search operations
    """
    def __init__(self):
        """
        Initialising Azure services
        """

        try:
            logger.info("Initialising Azure AI Search services")

            self.search_service_endpoint = secret_value.get_secret("AZURE_AI_SEARCH_ENDPOINT")
            self.search_service_key = secret_value.get_secret("AZURE_AI_SEARCH_API_KEY")
            self.search_index_name = os.environ["AZURE_AI_SEARCH_INDEX_NAME"]
            self.search_client = SearchClient(endpoint=self.search_service_endpoint, index_name=self.search_index_name,
                                              credential=AzureKeyCredential(self.search_service_key))

            consolidated_output_parser=self.consolidated_response_schema()
            insights_output_parser=self.insights_response_schema()
            report_output_parser=self.report_response_schema()
            consolidated_summary_template = config_db.query_prompt(source_name="Keyword_Digest", prompt_name="Consolidated_summary")
            insights_summary_template=config_db.query_prompt(source_name="Keyword_Digest", prompt_name="Insights_summary")
            report_summary_template= config_db.query_prompt(source_name="Keyword_Digest", prompt_name="Report_summary")
            consolidated_prompt = PromptTemplate(template=consolidated_summary_template,
                                                 input_variables=["raw_content", "clients_list", "keyword_name"],
                                                 partial_variables={"format_instructions":
                                                                        consolidated_output_parser.get_format_instructions()})
            self.consolidated_chain = consolidated_prompt | model | consolidated_output_parser

            insights_prompt = PromptTemplate(
                template=insights_summary_template,
                input_variables=["raw_content", "keyword_name", "clients_list"],
                partial_variables={"format_instructions": insights_output_parser.get_format_instructions()})

            self.insights_chain = insights_prompt | model | insights_output_parser

            report_prompt = PromptTemplate(
                template=report_summary_template,
                input_variables=["raw_content", "keyword_name", "clients_list"],
                partial_variables={"format_instructions": report_output_parser.get_format_instructions()})
            self.report_chain = report_prompt | model | report_output_parser
            # self.search_result_client_list = []
            # self.search_result_sentiment_list = []

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error initialising Azure services - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)

    def consolidated_response_schema(self):
        class consolidated_response_schema(BaseModel):
            news_summary: str = Field(description="Generate concise summary of the of given news article chunks according to given keyword.")
            keyword_relevance: Literal["true", "false"] = Field(
                description="Verify if the given news article chunks are relevant to the given keyword, true or false")
        output_parser = PydanticOutputParser(pydantic_object=consolidated_response_schema)
        return output_parser
    
    def insights_response_schema(self):
        class insights_response_schema(BaseModel):
            news_insights: str = Field(description="Generate key insights in bullet points for given news article chunks according to given keyword.")
            keyword_relevance: Literal["true", "false"] = Field(
                description="Verify if the given news article chunks are relevant to the given keyword, true or false")
        output_parser = PydanticOutputParser(pydantic_object=insights_response_schema)
        return output_parser
    
    def report_response_schema(self):
        class report_response_schema(BaseModel):
            news_report: str = Field(description="Generate detail report for given article content according to given keyword.")
            keyword_relevance: Literal["true", "false"] = Field(
                description="Verify if the given news article chunks are relevant to the given keyword, true or false")
        output_parser = PydanticOutputParser(pydantic_object=report_response_schema)
        return output_parser

    def generate_embeddings(self,chunk_list):
        """
        Function to generate embeddings
        """
        return embeddings.embed_documents(chunk_list)

    @staticmethod
    def convert_to_html_markdown(text):
        """
        Convert the text to markdown
        """
        results = markdown2.markdown(text)
        return results

ai_search = Azure_AI_Search()
class Keyword_Summarizer():
    
    def __init__(self, department,search_query, start_date, end_date, client_list):
        
        self.department=department
        self.search_query = search_query
        self.client_list = client_list
        self.start_date = start_date
        self.end_date = end_date
        self.news_chunks=[]
        self.news_links=[]
        self.news_output= []
        self.search_results=[]
     
    def get_search_results(self, source_list,department_flag=True,top_percentage_results_flag=True):
        """
        Function to get search results from Azure AI Search
        """
        try:
            print(f"Searching for keyword {self.search_query} from {self.start_date} to {self.end_date}")
            print(f"Searching for keyword {source_list} ")
            logger.info(f"Searching for keyword {self.search_query} from {self.start_date} to {self.end_date}")
            # making the time in ISO 8601 format
            time_with_midnight = "T00:00:00Z"
            start_date_str= self.start_date+time_with_midnight
            end_date_str= self.end_date+time_with_midnight

            # Creating the filter query
            date_range_filter_query = f"news_date ge {start_date_str} and news_date le {end_date_str}"

            if department_flag:
                # Creating the source name filter query
                # this is to avoid the source having "'" in their name
                escaped_source_list = [source.replace("'", "''") for source in source_list]
                source_name_filter_query = f"(search.in(source_name, '{','.join(escaped_source_list)}', ','))"

                # Creating the client name filter query
                self.client_list= self.client_list+["Others"]
                # this is to avoid the client having "'" in their name
                escaped_client_list = [client.replace("'", "''") for client in self.client_list]
                client_name_filter_query = f"(search.in(client_name, '{','.join(escaped_client_list)}', ','))"

                filter_query = client_name_filter_query + " and " + date_range_filter_query + " and " + source_name_filter_query

            else:
                filter_query=date_range_filter_query

            #create a vector search query
            vector_search_query = ai_search.generate_embeddings([self.search_query])[0]
            vector_query = [
                {
                    "vector": vector_search_query,
                    "k": int(os.environ['AZURE_SEARCH_TOP_K']),
                    "fields": "news_content_chunk_embedding",
                    "kind": "vector",
                    "exhaustive": True
                }
            ]
            results = ai_search.search_client.search(search_text= self.search_query,
                                                     query_type="full", ############
                                                     #vector_queries=vector_query, ########
                                                     top=int(os.environ['AZURE_SEARCH_TOP_K']),
                                                     filter=filter_query,### Need to check if department filter is required
                                                     include_total_count=True,
                                                     search_mode='all',# new
                                                     scoring_profile='Scoring_profile',
                                                     select=["id","source_name","client_name","news_title","news_url",
                                                             "news_date","news_summary","sentiment",
                                                             "news_content_chunk"])
            logger.info(f'Total Documents Matching Query:{results.get_count()}')
            #print(f'Total Documents Matching Query:{results.get_count()}')
            results=list(results)

            if not results:
                logger.info(f"No results found for the query {self.search_query}")
                return []
            # get max score
            max_score = results[0]['@search.score']

            self.filtered_data = [items for items in results if items['@search.score'] > max_score * 0.7]
            for items in self.filtered_data:
                if items['news_content_chunk'] not in self.news_chunks:
                    self.news_chunks.append(items['news_content_chunk'])
                if items["news_url"] not in self.news_links:
                    self.news_links.append(items["news_url"])

            if top_percentage_results_flag:
                thres_value= float(os.getenv("AZURE_AI_SEARCH_THRESHOLD","0.7"))
                print(thres_value, type(thres_value))                 
                return [items for items in results if items['@search.score'] > max_score * thres_value]
            else:
                return results

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error getting Search Results from Azure AI Search - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)
            raise Exception

    async def refine_search_results(self,results,emp_id,pageInformation):
        """
        Method to refine the search results
        It will remove the duplicate results and will return non-duplicate results
        """
        try:
            url_list=[]
            final_search_results=[]
            search_result_client_list=[]
            search_result_sentiment_list=[]
            for search_result in results: # results
                # remove duplicate results with a common url
                if search_result['news_url'] in url_list:
                    continue

                # Capitalize the sentiment   // to be removed later
                search_result['sentiment'] = search_result['sentiment'].capitalize()

                # get the unique values for all the keys
                if search_result['client_name'] not in search_result_client_list:
                    search_result_client_list.append(search_result['client_name'])
                if search_result['sentiment'] not in search_result_sentiment_list:
                    search_result_sentiment_list.append(search_result['sentiment'])

                # remove the fields that are not required
                if "@search.reranker_score" in search_result:
                    del search_result["@search.reranker_score"]
                if "@search.highlights" in search_result:
                    del search_result["@search.highlights"]
                if "@search.captions" in search_result:
                    del search_result["@search.captions"]
                if "news_content_chunk" in search_result:
                    del search_result["news_content_chunk"]

                url_list.append(search_result['news_url'])
                final_search_results.append(search_result)


            # Add feedback in the News Tile Summary
            final_search_results = [dict(item, **{'isThumbsUp': False, 'isThumbsDown': False}) for item in final_search_results]

            try:
                feedbacks = feedback_db.query_items(emp_id, pageInformation, self.search_query)
                if feedbacks:
                    final_search_results = helper.add_feedback_indicator(final_search_results, feedbacks)
                    logger.info(f'Added feedback in News Tile Summary for {emp_id}')
                else:
                    logger.info(f'No feedback available for user {emp_id}')
            except Exception as e:
                logger.error(f'Feedback Mechanism Error: {str(e)}')

            logger.info(f'Done with News Tile Summary for {self.search_query}')

            logger.info(f'Total Documents Matching Query:{ len(final_search_results)}')

            sentiment_sort_order=["Positive", "Negative", "Neutral"]
            sorted_search_sentiment_list=[sentiment for sentiment in sentiment_sort_order
                                          if sentiment in search_result_sentiment_list]
            search_result_client_list.sort()
            refined_result = {
                "client_list":search_result_client_list,
                "sentiment":sorted_search_sentiment_list,
                "search_data":final_search_results
            }
            return refined_result

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(
                f"Error getting Refined Search Results from Search results - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                stack_info=True)
            return []

    async def consolidated_summary(self):
        try:
            if self.news_chunks:
                start_time=time.time()
                output_dict = await ai_search.consolidated_chain.ainvoke(
                {"raw_content": self.news_chunks, "clients_list": self.client_list, "keyword_name": self.search_query})
                if output_dict.keyword_relevance == "true":
                    print(output_dict)
                    consolidated_output= output_dict.news_summary #+"<br>"+output_dict['client_summary']
                    end_time = time.time()
                    logger.info(f"Time taken for Consolidated Summarization is {end_time - start_time} seconds")
                    logger.info( f"Consolidated Summarization is successful for {self.search_query}")
                    return ai_search.convert_to_html_markdown(consolidated_output)
                else:
                    logger.info(f"Relevant news article not available for {self.search_query}")
                    return f"Relevant news articles not available for {self.search_query}"
            else:
                logger.info(f"Relevant news article not available for {self.search_query}")
                return f"Relevant news articles not available for {self.search_query}"

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in Generating the Consolidated Summary - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                            stack_info=True)
            return "Error in Generating the Consolidated Summary"

    async def insights_summary(self):
        try:
            if self.news_chunks:
                start_time=time.time()
                output_dict = await ai_search.insights_chain.ainvoke(
                {"raw_content": self.news_chunks, "clients_list": self.client_list, "keyword_name": self.search_query})
                if output_dict.keyword_relevance== "true":
                    print(output_dict)
                    insights_output= output_dict.news_insights
                    logger.info( f"Insights Summarization is successful for {self.search_query}")
                    end_time= time.time()
                    logger.info(f"Time taken for Insights Summarization is {end_time-start_time} seconds")
                    # returning after converting to markdown
                    return ai_search.convert_to_html_markdown(insights_output)
                else:
                    logger.info( f"Relevant news article not available for {self.search_query}")
                    return f"Relevant news article not available for {self.search_query}"
            else:
                logger.info( f"Relevant news article not available for {self.search_query}")
                return f"Relevant news article not available for {self.search_query}"

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in Generating the Insights Summary - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                            stack_info=True)
            return "Error in Generating the Insights Summary"

    async def report_summary(self):
        try:
            if self.news_chunks:
                start_time = time.time()
                output_dict = await ai_search.report_chain.ainvoke(
                {"raw_content": self.news_chunks, "clients_list": self.client_list, "keyword_name": self.search_query})
                if output_dict.keyword_relevance == "true":
                    report_output= output_dict.news_report
                    end_time = time.time()
                    logger.info(f"Time taken for Report Summarization is {end_time - start_time} seconds")
                    logger.info( f"Report Summarization is successful for {self.search_query}")
   
                    # returning after converting to markdown
                    return ai_search.convert_to_html_markdown(report_output)
                else:
                    logger.info( f"Relevant news article not available for {self.search_query}")
                    return f"Relevant news article not available for {self.search_query}"
            else:
                logger.info( f"Relevant news article not available for {self.search_query}")
                return f"Relevant news article not available for {self.search_query}"

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in Generating the report Summary - Line No: {exc_tb.tb_lineno}  Error: {str(e)}",
                            stack_info=True)
            return "Error in Generating the Market report Summary"
