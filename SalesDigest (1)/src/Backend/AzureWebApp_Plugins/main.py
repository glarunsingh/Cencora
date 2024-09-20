from dotenv import load_dotenv
_ = load_dotenv()
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from BingNews_Plugin import bing_news_plugin

import logging
# Set up logging to write to a file (optional)
logging.basicConfig(level=logging.INFO)#, filename="bing_plugin_log.log"
from BingNews_Plugin.utils.logger import create_log
logger = create_log(level=logging.INFO)
logger.propagate = True 

#To be checked
origins = [
    "http://localhost:8000",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:4700",
    "http://localhost:4700"
]

#allow_origins=origins,

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

app.include_router(bing_news_plugin.router)
if __name__ == "__main__":
    uvicorn.run('app:app', host="127.0.0.1", port=4700, reload=False)
