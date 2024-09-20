"""
File to load the open AI models
"""

import os
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings

import logging

logger = logging.getLogger(__name__)

AZURE_OPENAI_API_KEY = os.environ['AZURE_OPENAI_API_KEY']
model = AzureChatOpenAI(temperature=0.2,
                        openai_api_key=AZURE_OPENAI_API_KEY,
                        openai_api_version=os.environ['AZURE_OPENAI_API_VERSION'],
                        azure_deployment=os.environ['AZURE_OPENAI_DEPLOYMENT'],
                        azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
                        verbose=True)

embeddings = AzureOpenAIEmbeddings(openai_api_version=os.environ['EMBEDDINGS_API_VERSION'],
                                   azure_endpoint=os.environ['EMBEDDINGS_ENDPOINT'],
                                   openai_api_key=os.environ['EMBEDDINGS_API_KEY'],
                                   model=os.environ['EMBEDDINGS_MODEL'],
                                   deployment=os.environ['EMBEDDINGS_DEPLOYMENT'])

Token_Count = os.getenv('TOKEN_COUNT')
