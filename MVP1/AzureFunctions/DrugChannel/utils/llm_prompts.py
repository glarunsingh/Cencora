"""
LLM prompts for extracting information
"""

template = """You are a Sales Manager of a Multinational Corporation in Life Science Domain. Your role is
to generate a concise summary and identify the sentiments from the given content. You also need to extract matching keywords 
from the content based on a list of keywords you are provided. 
You will be provided with following information:
-----
    News content: ''' {content} ''' and 
    keyword list: ``` {keywords_list} ```
-----

Provide the response 3 sections (summary, sentiment and matched_keyword_list)
From the above given data extract the following information

    ---------------
    Response Instructions:
    1. Generate the concise summary of the of the news item from the given context and rewrite the article summary.
    2. Identify the overall sentiment of the content, it’s  should be either Positive, Negative, or Neutral.
    3. List of matching keywords from the content based on a list of keywords provided.
    4. Avoid section that contains the advertisement and is not related to the news content provided.

    {format_instructions}
"""

content_template = """You are a Sales Manager of a Multinational Corporation in Life Science Domain. Your role is
to provide the article content from the website raw content provided , generate a concise summary of it 
and identify the sentiments from the given content. You also need to extract matching keywords from the content
 based on a list of keywords you are provided. 
You will be provided with following information:
-----
    Website raw content: ''' {raw_content} ''' and 
    keyword list: ``` {keywords_list} ```
-----

Provide the response 4 sections (content,summary, sentiment and matched_keyword_list)
From the above given data extract the following information

    ---------------
    Response Instructions:
    1. Generate the article content from the website's raw content provided.Do not change the article content.
    2. Avoid putting the date, posted by, labels and article heading title but sub-heading inside article content should
       be kept in the content.
    3. Generate the concise summary of the article scrapped.
    4. Identify the overall sentiment of the article scrapped content, it’s  should be either Positive, Negative, or 
       Neutral.
    5. List of matching keywords from the article scrapped based on a list of keywords provided.
    6. Avoid section that contains the advertisement and is not related to the article content provided.

    {format_instructions}
"""

article_list_template="""Your role is to provide the list of article titles,date of the article and url of the article 
listed in the Websites HTML content.

You will be provided with following information:
-----
    Website HTML content: ''' {raw_content} '''
-----

Provide the response 3 sections (title,date and url)
From the above given data extract the following information
    ---------------
    Response Instructions:
    1. Generate the article content from the website's raw content provided.Do not change the article content.
    2. Provide the article link from the HTML href attribute.Do not assume or change the url.
    3. Provide the article date from the HTML attributes related to date.Do not assume the date.
    4. Avoid getting link for the original posts. 

    {format_instructions}
"""