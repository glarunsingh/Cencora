import logging
import sys

import requests
import tiktoken
from bs4 import BeautifulSoup
from langchain.chains import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from utils.LLM_prompts import Stuff_prompt
from utils.load_model import AZURE_OPENAI_API_KEY,model,embeddings,Token_Count
from utils.logs import create_log

logger = create_log(name="Drug_Channel", level=logging.INFO)


async def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


async def get_summary(raw_text, date,url):
    try:
        if len(raw_text) > 2.7 * int(Token_Count):
            tokens = await num_tokens_from_string(raw_text, "cl100k_base")
            if tokens > int(Token_Count):
                text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=8000, chunk_overlap=600)
                docs = [Document(page_content=x) for x in text_splitter.split_text(raw_text)]
                chain = load_summarize_chain(model,chain_type="map_reduce",prompt= Stuff_prompt)
        else:
            docs = [Document(page_content=str(raw_text), metadata={"date": date})]
            chain = load_summarize_chain(model, chain_type="stuff" )
        summary = chain.invoke({"input_documents": docs})
        logger.info(f"Summarization Complete")
        return summary['output_text']

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Unable to summarize content.Hence Skipping! Url: {url} - Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return None
