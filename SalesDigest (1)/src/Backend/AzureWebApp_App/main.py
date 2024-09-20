from dotenv import load_dotenv
_ = load_dotenv()

import logging
from config import logger_setup

logging.basicConfig(level=logging.INFO)
logger = logger_setup.create_log(level=logging.INFO)
logger.propagate = True

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from main_app import dependencies, keyword_digest
from onboarding_page import onboarding
from feedback_page import feedback


#To be checked
origins = [
    "http://localhost:8000",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:4700",
    "http://localhost:4700",
    "https://stfckeyaccountqa.z20.web.core.windows.net"
]

# allow_origins=origins,

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

app.include_router(dependencies.router)
app.include_router(onboarding.router)
app.include_router(keyword_digest.router)
app.include_router(feedback.router)


if __name__ == "__main__":
    uvicorn.run('app:app', host="127.0.0.1", port=4700, reload=False)
