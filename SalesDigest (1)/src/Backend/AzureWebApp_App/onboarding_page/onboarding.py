import sys
import time
from typing import List, Optional

import uvicorn
from fastapi import HTTPException, Response, status, APIRouter, Depends
from pydantic import BaseModel, Field, EmailStr

from Authentication.auth import validate_user
from onboarding_page.utils.db_function import DBOPS

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/onboarding',
                   tags=['onboarding'])

db_ops = DBOPS()


@router.get('/init', tags=['Onboarding Page'])
async def get_user_details_via_token(response: Response, token_details: dict = Depends(validate_user)):
    """
    Function to get user details from the token and sending it to Frontend.
    """
    try:
        user_detail = db_ops.get_user_details(token_details['emp_id'])
        if user_detail:
            token_details['isOnboarded'] = True
            if token_details['department_name'] == 'All':
                token_details['department_name'] = user_detail['department_name']
            if token_details['department_name'] != 'All' and (
                    user_detail['department_name'] != token_details['department_name']):
                db_ops.update_user_details_based_on_token(user_detail, token_details)
        else:
            token_details['isOnboarded'] = False
            if token_details['department_name'] == 'All':
                token_details['department_name'] = ''
        return {'success': True, 'message': 'User Details Extracted Successfully', 'data': token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'success': False, 'message': "User Details Extraction Failed!", "data": []}


@router.get('/get_departments', tags=['Onboarding Page'])
async def get_department_name(response: Response,
                              token_details: dict = Depends(validate_user)):
    """
        This function retrieves the department names from the database.

        Args:
            response (Response): The response object.

        Returns:
            dict: A dictionary containing the success status, message, and data.

        Raises:
            Exception: If there is an error retrieving the department names.
    """
    try:
        start_time = time.time()
        results = db_ops.get_department_name()
        end_time = time.time()
        logger.info(f'Department name extracted! Time: {end_time - start_time} '
                    f'Container: {db_ops.CLIENT_INF_CONTAINER_NAME}')
        response.status_code = status.HTTP_200_OK
        return {'success': True, 'message': "Department name extracted!", "data": results,
                "user_details": token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'success': False, 'message': "Department name extraction Failed!", "data": []}


@router.get('/get_clients_name/{department}', tags=['Onboarding Page'])
async def get_clients_name(department, response: Response, token_details: dict = Depends(validate_user)):
    """
        Retrieves the clients' names based on the department provided.

        Args:
            department (str): The department for which clients' names are to be retrieved.
            response (Response): The response object.

        Returns:
            dict: A dictionary containing the success status, message, and data.
    """
    try:
        start_time = time.time()
        results = db_ops.get_clients_name(department)
        sorted_results = sorted(results)
        end_time = time.time()
        logger.info(f"Clients name extracted! {department} Time: {end_time - start_time} "
                    f"Container: {db_ops.CLIENT_INF_CONTAINER_NAME}")
        response.status_code = status.HTTP_200_OK
        return {'success': True, 'message': "Clients name extracted!", "data": sorted_results}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'success': False, 'message': "Clients name extraction Failed!", "data": [],
                "user_details": token_details}


class UserDetails(BaseModel):
    # UserDetails class for defining user details
    emp_id: str = Field(description='Employee(oid) id of the user')
    first_name: str = Field(description='First name of the user')
    last_name: str = Field(description='Last name of the user')
    email_id: EmailStr = Field(description='Email id of the user')
    favourite_client_list: List[str] = Field(default=[],
                                             description='List of favourite client of user')
    email_notify: bool = Field(default=False,
                               description='User Authorization for email subscription')
    department_name: str = Field(description='Department name of the user')


class ManageAccount_UserDetails(BaseModel):
    """
        Model class for managing user details in an account.
    """
    emp_id: str = Field(description='Employee(oid) id of the user')
    first_name: str = Field(description='First name of the user')
    last_name: str = Field(description='Last name of the user')
    email_id: EmailStr = Field(description='Email id of the user')
    favourite_client_list: List[str] = Field(default=[],
                                             description='List of favourite client of user')
    department_name: str = Field(description='Department name of the user')
    department_change : Optional[bool] = Field(default=False, description='is there a Department change of the user')
    email_notify: bool = Field(default=False, description='User Authorization for email subscription')


@router.post('/user_details', tags=['Onboarding Page'])
async def user_details(details: UserDetails, token_details: dict = Depends(validate_user)):
    """
        Endpoint to update user details.

        Args:
            details (UserDetails): User details to be updated.

        Returns:
            dict: A dictionary indicating the success status and a message.

        Raises:
            HTTPException: If there is an error updating the user details.
    """
    try:
        start_time = time.time()
        db_ops.update_client_data(details)
        end_time = time.time()
        logger.info(f"Users Details stored successfully! {end_time - start_time} "
                    f"Container: {db_ops.CLIENT_INF_CONTAINER_NAME}")
        return {'success': True, 'message': "User details updated!",
                "user_details": token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        # raise HTTPException(status_code=500, detail="Error updating details")
        return {'success': False, 'message': "User details update Failed!"}


@router.post('/non_admin_save_fav_client', tags=['Manage Account(Member)'])
async def update_favclient_non_admin_user(details: ManageAccount_UserDetails,
                                          token_details: dict = Depends(validate_user)):
    """
       Updates the favorite client list for a non-admin user.

       Args:
           details (ManageAccount_UserDetails): The details of the user.

       Returns:
           dict: A dictionary with the success status and a message.

       Raises:
           HTTPException: If there is an error updating the details.
    """
    try:
        start_time = time.time()
        user_details = db_ops.get_user_details(details.emp_id)

        #Only admin will be allowed to change the department
        if token_details['role'] not in ['Admin']:
            details.department_change = False

        # if only department change is there for user
        old_department = user_details["department_name"]
        if details.department_change and old_department != details.department_name:
            user_details["department_name"] = details.department_name
            user_details["favourite_client_list_"+old_department] = user_details['favourite_client_list']
            user_details["favourite_client_list"] = user_details.get("favourite_client_list_"+details.department_name,[])

        else:
            user_details["favourite_client_list"] = details.favourite_client_list

        user_details["email_notify"] = details.email_notify
        db_ops.upsert_items(user_details, db_ops.USER_DATA_CONTAINER)
        end_time = time.time()
        logger.info(f"Users favourite client details updated successfully! {end_time - start_time} "
                    f"Container: {db_ops.USER_DATA_CONTAINER}")
        return {'success': True, 'message': "User details updated!",
                "user_details": token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        #raise HTTPException(status_code=500, detail="Error updating details")
        return {'success': False, 'message': "User details update Failed!"}


class Manage_Client_Modification_schema(BaseModel):
    """
       Schema Class to manage add/modify client name by admins in manage account page.
    """
    client_uuid: Optional[str] = None
    client_name: str
    synonyms: str
    department_name: str
    last_updated_by: str
    last_updated_on: str


class Manage_Client_Modification(BaseModel):
    """
    Class to manage add/modify client name by admins in manage account page.
    """
    values: List[Manage_Client_Modification_schema]


@router.post('/admin_save_client_modification', tags=["Manage Account(Admin)"])
async def save_admin_client_modifications(values: Manage_Client_Modification,
                                          token_details: dict = Depends(validate_user)):
    """
        Manage add/modify client name by admins in manage account page.

        Args:
            details (Manage_Client_Modification): The details of the client modification.

        Returns:
            dict: A dictionary with the success status and a message.

        Raises:
            HTTPException: If there is an error updating the details.
        """
    if token_details['role'] not in ['Admin']:
        raise HTTPException(status_code=401, detail="Unauthorised Access for the User")
    try:
        start_time = time.time()
        details_list = values.values
        for details in details_list:
            item = {"client_name": details.client_name, "synonyms": details.synonyms,
                    "department_name": details.department_name, "last_updated_by": details.last_updated_by,
                    "last_updated_on": details.last_updated_on}
            if details.client_uuid:
                item["id"] = details.client_uuid
            else:
                # Updated the client id to be sum of client name and department from the last release
                client_id = details.client_name + details.department_name
                item["id"] = db_ops.sha_conversion(client_id)
            db_ops.upsert_items(item, db_ops.CLIENT_INF_CONTAINER_NAME)
            end_time = time.time()
            logger.info(f"Client Details changed successfully! {end_time - start_time}s "
                        f"Container: {db_ops.CLIENT_INF_CONTAINER_NAME} Client Name: {details.client_name}")
        return {'success': True, 'message': "User details updated!",
                "user_details": token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'success': False, 'message': "User details update failed!"}
        # return {'success': False, 'message': "User details update Failed!"}


class Delete_Admin_Client_Modification(BaseModel):
    """
    Model for deleting an admin client modification.
    """
    client_uuid: str
    client_name: str
    department_name: str


@router.post('/delete_client_admin', tags=["Manage Account(Admin)"])
async def delete_admin_client_modifications(details: Delete_Admin_Client_Modification,
                                            token_details: dict = Depends(validate_user)):
    """
        Deletes a client modification made by an admin.

        Args:
            details (Delete_Admin_Client_Modification): The details of the client modification.
            token_details (dict, optional): The user details. Default Depends(validate_user).

        Returns:
            dict: A dictionary with the success status and a message.

        Raises:
            HTTPException: If the user is not an admin.
    """
    if token_details['role'] not in ['Admin']:
        raise HTTPException(status_code=401, detail="Unauthorised Access for the User")
    try:
        start_time = time.time()
        # client_id = db_ops.get_client_id(details.client_name, details.department_name)
        db_ops.delete_items(details.client_uuid, details.department_name, db_ops.CLIENT_INF_CONTAINER_NAME)
        end_time = time.time()
        logger.info(f"Clients Details Deleted successfully! {end_time - start_time} "
                    f"Client Name: '{details.client_name}' Container: {db_ops.CLIENT_INF_CONTAINER_NAME}")
        return {'success': True, 'message': "Client details deleted",
                "user_details": token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'success': False, 'message': "Client name deletion failed"}


class Manage_keyword_Modification_schema(BaseModel):
    """
       Schema Class to manage add/modify keyword name by admins in manage account page.
    """
    keyword_uuid: Optional[str] = None
    keyword_name: str
    department_name: str
    last_updated_by: str
    last_updated_on: str


class Manage_keyword_Modification(BaseModel):
    """
    Class to manage add/modify keyword name by admins in manage account page.
    """
    values: List[Manage_keyword_Modification_schema]


@router.post('/admin_save_keywords_modification', tags=["Manage Account(Admin)"])
async def save_admin_keywords_modifications(values: Manage_keyword_Modification,
                                            token_details: dict = Depends(validate_user)):
    """
        Manage add/modify keyword name by admins in manage account page.

        Args:
            details (Manage_keyword_Modification): The details of the keyword modification.

        Returns:
            dict: A dictionary with the success status and a message.

        Raises:
            HTTPException: If there is an error updating the details.
    """
    if token_details['role'] not in ['Admin']:
        raise HTTPException(status_code=401, detail="Unauthorised Access for the User")
    try:
        start_time = time.time()

        details_list = values.values
        for details in details_list:
            item = {"keyword_name": details.keyword_name, "department_name": details.department_name,
                    "last_updated_by": details.last_updated_by, "last_updated_on": details.last_updated_on}
            if details.keyword_uuid:
                item["id"] = details.keyword_uuid
            else:
                keyword_id = details.keyword_name + details.department_name
                item["id"] = db_ops.sha_conversion(keyword_id)
            db_ops.upsert_items(item, db_ops.KEY_CONTAINER_NAME)
            end_time = time.time()
            logger.info(f"Keywords Details changed successfully! {end_time - start_time}s "
                        f"Container: {db_ops.KEY_CONTAINER_NAME} Keyword Name: {details.keyword_name}")
        return {'success': True, 'message': "User details updated!",
                "user_details": token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'success': False, 'message': "User details update failed!"}

class Delete_Admin_Keywords_Modification(BaseModel):
    """
    Model for deleting an admin keywords modification.
    """
    keyword_uuid: str
    keyword_name: str
    department_name: str


@router.post('/delete_keywords_admin', tags=["Manage Account(Admin)"])
async def delete_admin_keyword_modifications(details: Delete_Admin_Keywords_Modification,
                                            token_details: dict = Depends(validate_user)):
    """
        Deletes a keyword modification made by an admin.

        Args:
            details (Delete_Admin_Keywords_Modification): The details of the keyword modification.
            token_details (dict): The details of the user making the request.

        Returns:
            dict: A dictionary with the success status and a message.

        Raises:
            HTTPException: If the user is not authorized or if there is an error deleting the details.
    """
    if token_details['role'] not in ['Admin']:
        raise HTTPException(status_code=401, detail="Unauthorised Access for the User")
    try:
        start_time = time.time()
        db_ops.delete_items(details.keyword_uuid, details.department_name, db_ops.KEY_CONTAINER_NAME)
        end_time = time.time()
        logger.info(f"Keywords Details Deleted successfully! {end_time - start_time} "
                    f"Keyword Name: '{details.keyword_name}' Container: {db_ops.KEY_CONTAINER_NAME}")
        return {'success': True, 'message': "Keyword details deleted",
                "user_details": token_details}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        return {'success': False, 'message': "Keyword name deletion failed"}


if __name__ == "__main__":
    uvicorn.run('app:app', host="127.0.0.1", port=4200, reload=False)
