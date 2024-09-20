from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
import faiss
import pickle
import numpy as np
import logging

from utils.logs import create_log
from utils.load_model import model, embeddings


logger = create_log(name="chatbot", level=logging.INFO)

def embeddings_the_data(extracted_data):

    # Assuming `extracted_data` contains the news content as a string
    # Split the extracted data into smaller chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_text(extracted_data)

    # Generate embeddings for each chunk
    embeddings_list = [embeddings.embed_documents(text) for text in texts]

    # Create a Faiss index
    dimension = len(embeddings_list[0])  # assuming all embeddings have the same dimension
    index = faiss.IndexFlatL2(dimension)

    # Add embeddings to the index
    index.add(np.array(embeddings_list))

    # Save the Faiss index and texts for retrieval
    faiss.write_index(index, 'faiss_index.bin')
    with open('texts.pkl', 'wb') as f:
        pickle.dump(texts, f)


def load_faiss_index_and_texts(index_path: str, texts_path: str):
    try:
        index = faiss.read_index(index_path)
        with open(texts_path, 'rb') as f:
            texts = pickle.load(f)
        return index, texts
    except Exception as e:
        logger.error(f"Error loading Faiss index or texts: {str(e)}")
        raise


