import numpy as np
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.chains.question_answering import load_qa_chain
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.faiss import FAISS
import logging
#from utils.embedding import embeddings
from utils.load_model import model, embeddings

from utils.logs import create_log

# Create a logger
logger = create_log(name="chatbot", level=logging.INFO)


def search_vector_store(query: str, index, texts, num_results: int = 3):
    try:
        # Generate the embedding for the query
        query_embedding = embeddings.embed(query)
        
        # Search in the vector store
        distances, indices = index.search(np.array([query_embedding]), num_results)
        
        # Retrieve the relevant texts
        results = [(texts[i], distances[0][idx]) for idx, i in enumerate(indices[0])]
        return results
    except Exception as e:
        logger.error(f"Error searching vector store: {str(e)}")
        raise


def get_conversation_chain():
    # Initialize conversation memory
    memory = ConversationBufferMemory()

    # Load the QA chain
    qa_chain = load_qa_chain(model, memory=memory)

    return qa_chain


async def answer_question_with_memory(question: str, index, texts, qa_chain):
    try:
        # Retrieve relevant documents from the vector store
        results = search_vector_store(question, index, texts)

        # Extract the most relevant document
        relevant_docs = [result[0] for result in results]

        # Generate the answer with conversation memory
        answer = await qa_chain.arun(input_documents=relevant_docs, question=question)
        return answer
    except Exception as e:
        logger.error(f"Error answering question with memory: {str(e)}")
        raise
