import os
import requests
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set your Azure OpenAI API key and endpoint
api_key = os.getenv('AZURE_OPENAI_API_KEY')
endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
deployment_id = os.getenv('AZURE_OPENAI_DEPLOYMENT_ID')

# Initialize ChromaDB client
client = chromadb.Client()

# Define the path to the directory containing the text files
directory_path = 'path_to_your_text_files'

# Function to get embeddings from Azure OpenAI
def get_azure_openai_embeddings(text):
    url = f"{endpoint}openai/deployments/{deployment_id}/embeddings"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    payload = {
        "input": text
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    embeddings = response.json()['data'][0]['embedding']
    return embeddings

# Function to read text files and convert to embeddings
def process_files(directory_path):
    data = []

    # Iterate through all text files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

                # Get embeddings for the text
                embeddings = get_azure_openai_embeddings(text)

                # Prepare data for ChromaDB
                data.append({
                    'file_name': filename,
                    'text': text,
                    'embedding': embeddings
                })

    return data

# Process the text files
data = process_files(directory_path)

# Define a schema for your ChromaDB collection
schema = {
    'file_name': 'string',
    'text': 'string',
    'embedding': 'vector<float>'
}

# Create a ChromaDB collection
collection = client.create_collection('text_embeddings', schema)

# Insert data into the ChromaDB collection
for item in data:
    collection.insert(item)

print('Data successfully inserted into ChromaDB.')
