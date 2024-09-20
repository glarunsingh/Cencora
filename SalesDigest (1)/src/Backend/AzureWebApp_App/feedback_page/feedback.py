import sys
import time
from typing import List, Optional
import hashlib

import uvicorn
from fastapi import HTTPException, Response, status, APIRouter, Depends
from pydantic import BaseModel, Field, EmailStr

from Authentication.auth import validate_user
from feedback_page.utils.db_helper import DBOPS
# from onboarding_page.utils.db_function import DBOPS
from typing import Literal

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/feedback',
                   tags=['feedback'])

db_ops = DBOPS()

class User_Feedback(BaseModel):
    """
        Model class for managing user feedback.
        {
        news_url:"xxxxx.html",
        emp_id:"xxx",
        first_name:"xxxxx",
        last_name:"xxxxx",
        feedback:"isThumbsUp/isThumbsDown",
        value:true/false,
        category:"xxxxx",
        comment:"xxxxxx",
        pageInformation:"xxxx"
        }
    """
    emp_id: str = Field(description='Employee(oid) id of the user')
    first_name: str = Field(description='First name of the user')
    last_name: str = Field(description='Last name of the user')

    news_url: str = Field(description='News url of user feedback')
    feedback: Literal ["isThumbsUp", "isThumbsDown"] = Field(description='User feedback,  isThumbsUp or isThumbsDown')
    # value: Literal [True, False] = Field(description= 'True or False')
    value: bool = Field(description= 'True or False')
    category: str = Field(description='What is the feedback category')
    comment: str = Field(description='Reson behind providing feedback')
    pageInformation: str = Field(description='Page Information')
    search_query: Optional[str] = Field(description='Query Searched by user',default ="")

def sha_conversion(data: str) -> str:
        sha256 = hashlib.sha256(data.encode('utf-8')).hexdigest()
        return sha256

@router.post('/update_user_feedback', tags=['feedback'])
async def update_user_feedback(details: User_Feedback,
                                        token_details: dict = Depends(validate_user)):
#async def update_user_feedback(details: User_Feedback,
#                                          token_details = None):
    """
       Update user feedback.
       Args:
           details (User_Feedback): The details of the user feedback.
       Returns:
           dict: A dictionary with the success status and a message.
       Raises:
           HTTPException: If there is an error updating the details.
    """
    try:
        user_feedback = {}
        start_time = time.time()
        user_feedback['id'] = sha_conversion(details.emp_id+details.news_url+details.pageInformation)
        user_feedback["emp_id"] = details.emp_id
        user_feedback["first_name"] = details.first_name
        user_feedback["last_name"] = details.last_name
        user_feedback["news_url"] = details.news_url
        user_feedback["feedback"] =  "positive" if details.feedback == "isThumbsUp" else "negative" ####
        user_feedback["category"] = details.category
        user_feedback["comment"] = details.comment
        user_feedback["pageInformation"] = details.pageInformation
        user_feedback["search_query"] = details.search_query.strip().lower()  # to remove extra white space and convert to lower case

        if details.value:
            db_ops.upsert_items(user_feedback)
            end_time = time.time()
            logger.info(f"User's feedback details updated successfully! {end_time - start_time} ")
            return {'success': True, 'message': "User's feedback updated!",
                    "user_details": token_details}
        else:
            delete_indicator = db_ops.delete_items(user_feedback['id'] , details.emp_id)
            end_time = time.time()
            if delete_indicator:
                logger.info(f"User's feedback details deleted successfully! {end_time - start_time} ")
                return {'success': True, 'message': "User's feedback removed!",
                        "user_details": token_details}
            else:
                logger.info(f"User's details not found in feedback table! {end_time - start_time} ")
                return {'success': False, 'message': "User's details not found in feedback table!",
                        "user_details": token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        #raise HTTPException(status_code=500, detail="Error updating details")
        return {'success': False, 'message': "User's feedback update Failed!"}