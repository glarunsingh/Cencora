import logging
import time
import os
from dotenv import load_dotenv
import asyncio

from utils.logs import create_log
from utils.cosmos_function import chatbotdb
from utils.embedding import embeddings_the_data, load_faiss_index_and_texts
from utils.vectorsearch import get_conversation_chain, answer_question_with_memory

import faiss
import pickle
import numpy as np
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.chains.question_answering import load_qa_chain
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.faiss import FAISS
import logging

_ = load_dotenv('./config/db.env')
logger = create_log(name="chatbot", level=logging.INFO)
cron_time = os.getenv('CHATBOT_CRON')
department = None


async def chatbot():
    start_time = time.time()
    logger.info("Extracting information from cosmosdb")

    db_ops = chatbotdb()

    # Query the DB to get the latest news content
    latest_news_content = db_ops.get_latest_news_content()
    return latest_news_content


if __name__ == "__main__":
    async def main():
        extracted_data = await chatbot()
        print(extracted_data)
        embeddings_the_data(extracted_data)

        # Load the Faiss index and texts
        index, texts = load_faiss_index_and_texts('faiss_index.bin', 'texts.pkl')
        qa_chain = get_conversation_chain()

        # Example conversation loop
        while True:
            user_question = input("User: ")
            if user_question.lower() in ["exit", "quit"]:
                logger.info("Ending session")
                break
            
            # Answer the question
            answer = await answer_question_with_memory(user_question, index, texts, qa_chain)
            print(f"Bot: {answer}")

            # Optional: You can clear the memory here if needed
            # qa_chain.memory.clear()
    
    asyncio.run(main())
