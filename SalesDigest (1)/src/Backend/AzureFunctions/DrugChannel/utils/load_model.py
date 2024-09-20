"""
File to load the open AI models
"""

import os
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings

import logging
logger = logging.getLogger(__name__)

AZURE_OPENAI_API_KEY = os.environ['AZURE_OPENAI_API_KEY'] #session_var.AZURE_OPENAI_API_KEY  #secret_value.get_secret('AZURE-OPENAI-API-KEY')

model = AzureChatOpenAI(temperature=0.2,
                        openai_api_key=AZURE_OPENAI_API_KEY,
                        openai_api_version=os.environ['AZURE_OPENAI_API_VERSION'], #os.getenv("AZURE_OPENAI_API_VERSION"),
                        azure_deployment=os.environ['AZURE_OPENAI_DEPLOYMENT'],#os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                        azure_endpoint= os.environ['AZURE_OPENAI_ENDPOINT'],##session_var.AZURE_OPENAI_ENDPOINT,  #secret_value.get_secret("AZURE-OPENAI-ENDPOINT"),
                        verbose=True)

embeddings = AzureOpenAIEmbeddings(openai_api_version= os.environ['EMBEDDINGS_API_VERSION'],#os.getenv("EMBEDDINGS_API_VERSION"),
                                   azure_endpoint= os.environ['EMBEDDINGS_ENDPOINT'],#session_var.EMBEDDINGS_ENDPOINT, #secret_value.get_secret("EMBEDDINGS-ENDPOINT"),
                                   openai_api_key= os.environ['EMBEDDINGS_API_KEY'],#session_var.EMBEDDINGS_API_KEY, #secret_value.get_secret("EMBEDDINGS-API-KEY"),
                                   model=os.environ['EMBEDDINGS_MODEL'],#session_var.EMBEDDINGS_MODEL, #secret_value.get_secret("EMBEDDINGS-MODEL"),
                                   deployment=os.environ['EMBEDDINGS_DEPLOYMENT'] #session_var.EMBEDDINGS_DEPLOYMENT #secret_value.get_secret("EMBEDDINGS-DEPLOYMENT")
                                   )

Token_Count = os.getenv('TOKEN_COUNT')
