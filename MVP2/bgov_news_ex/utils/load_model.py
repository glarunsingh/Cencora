import os
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from dotenv import load_dotenv

_ = load_dotenv('./config/llm.env')

AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')

model = AzureChatOpenAI(temperature=0.2,
                        openai_api_key=AZURE_OPENAI_API_KEY,
                        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                        verbose=True)

embeddings = AzureOpenAIEmbeddings(openai_api_version=os.getenv("EMBEDDINGS_API_VERSION"),
                                   azure_endpoint=os.getenv("EMBEDDINGS_ENDPOINT"),
                                   openai_api_key=os.getenv("EMBEDDINGS_API_KEY"),
                                   model=os.getenv("EMBEDDINGS_MODEL"),
                                   deployment=os.getenv("EMBEDDINGS_DEPLOYMENT")
                                   )

Token_Count = os.getenv('TOKEN_COUNT')
