import json
import os

def save_news_data(news_data, json_file_path):
    try:
        with open(json_file_path, 'w') as json_file:
            json.dump(news_data, json_file, indent=4)
    except IOError as e:
        print(f'Error saving JSON file: {e}')