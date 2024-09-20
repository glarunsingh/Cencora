import sys
from fastapi import Depends, HTTPException, Request, WebSocket, WebSocketException, status
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordBearer

import logging
logger = logging.getLogger(__name__)

from Authentication.auth_utils import Authentication

auth = Authentication()
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{auth.authority}/oauth2/v2.0/authorize",
    tokenUrl=f"{auth.authority}/oauth2/v2.0/token"
)

################  token: str = Depends(oauth2_scheme) ////// to be added inside validate_user
def validate_user(token: str = Depends(oauth2_scheme)):
    #, role=['Admin'], department=['All']
    #####################``
    # logger.info("\n\n\n\n\n")
    # token=000
    # logger.info(f"token: {token}")
    # return {
    #     'unique_name': "test",
    #     'department_name':    "All",
    #     'role': "Admin"
    # }

    #################
    payload = auth.validate_token(token)
    try:
        token_department, token_access = auth.get_dept_access_values(payload['roles'])
        # Check for the access role of the API
        user_details = {
            "emp_id": payload['oid'],
            'first_name': payload['given_name'],
            'last_name': payload['family_name'],
            'unique_name': payload['unique_name'],
            'department_name': token_department,
            'role': token_access
        }
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        raise HTTPException(status_code=401, detail="Invalid User")

    return user_details



#### create custom OAuth2PasswordBearer for websocket ####
class CustomOAuth2PasswordBearer(OAuth2PasswordBearer):
    async def __call__(self, request: Request = None, websocket: WebSocket = None):
        return await super().__call__(request or websocket)


websocket_oauth2_scheme = CustomOAuth2PasswordBearer(tokenUrl="login")

def websocket_validate_user(token: str = Depends(websocket_oauth2_scheme)):
    #, role=['Admin'], department=['All']
    #####################``
    # logger.info("\n\n\n\n\n")
    # token=000
    # logger.info(f"token: {token}")
    # return {
    #     'unique_name': "test",
    #     'department_name':    "All",
    #     'role': "Admin"
    # }

    #################
    payload = auth.validate_token(token, websocket=True)
    try:
        token_department, token_access = auth.get_dept_access_values(payload['roles'])
        # Check for the access role of the API
        user_details = {
            "emp_id": payload['oid'],
            'first_name': payload['given_name'],
            'last_name': payload['family_name'],
            'unique_name': payload['unique_name'],
            'department_name': token_department,
            'role': token_access
        }
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid User")

    return user_details
