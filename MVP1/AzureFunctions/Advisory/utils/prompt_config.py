"""
config file for news digest
"""

NEWS_PROMPT = """Your role is identify the sentiments from the given content 
and generate a concise summary of the given content. You also need to extract matching keywords 
from the content based on a list of keywords you provide. 
You will be provided with following information:
-----
    News content: ''' {content} ''' and 
    keyword list: ``` {keyword_list} ```
-----

Provide the response 3 sections (summary, sentiment and matched_keyword_list)
From the above given data extract the following information

    ---------------
    Response Instructions:
    1. Generate the concise summary of the of the news item from the given context and rewrite the article summary.
    2. Identify the overall sentiment of the content, whether it’s positive, negative, or neutral.
    3. List of matching keywords from the content based on a list of keywords provided.

    {format_instructions}
"""

prompt_config = {"news_prompt":NEWS_PROMPT
                }
