import base64
import json
import os
import sys
import jwt
import requests
from fastapi import HTTPException, WebSocketException,status
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from config.key_vault import key_vault
secret_value = key_vault()

import logging
logger = logging.getLogger(__name__)

class Authentication:
    def __init__(self):
        self.tenant_id = secret_value.get_secret("TENANT-ID")
        self.client_id = secret_value.get_secret('CLIENT-ID')
        self.algorithms = [secret_value.get_secret('ACCESS-TOKEN-ALGORITHM')]
        self.audience = f"api://{self.client_id}"
        self.issuer_url = secret_value.get_secret("ISSUER-URL")
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.public_key_url = f"{self.authority}/discovery/keys"
        self.department_dict = {
            'HealthSystems': 'Health systems',
            'Government': 'Government sales',
            'Triose': 'Triose',
            'Global': 'All'
        }

    def get_dept_access_values(self, roles):
        """
        Get the department and access values from the given roles.
        """

        # this if statement needs to be removed if the Entra ID have only unique roles
        if "Global.Admin" in roles:
            roles = ["Global.Admin"]
        roles_list = roles[0].split('.')
        department_name = roles_list[0]
        department = self.department_dict[
            department_name] if department_name in self.department_dict else department_name
        access = roles_list[1]
        return department, access

    def validate_token(self, token: str,websocket=False):
        """
        Function to validate Token
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
            ad_key = self.get_public_keys(unverified_header["kid"])
            #logger.info(f"key:{ad_key}")
            key = self.rsa_pem_from_jwk(ad_key)
            options = {"verify_signature": True, "verify_aud": True, "require": ["exp", "iat", "nbf"],
                       "verify_iss": True, "verify_exp": True, "verify_iat": True, "verify_nbf": True,
                       "strict_aud": True}
            payload = jwt.decode(token, key=key, algorithms=self.algorithms, audience=self.audience,
                                 issuer=self.issuer_url, verify=True,
                                 options=options)
            return payload
        except jwt.ExpiredSignatureError:
            message="Invalid User: Expired Token"
            if websocket:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION,reason=message)
            raise HTTPException(status_code=401, detail=message)

        except jwt.InvalidIssuedAtError:
            message="Invalid User: Invalid Issued At"
            if websocket:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=message)
            raise HTTPException(status_code=401, detail=message)

        except jwt.MissingRequiredClaimError:
            message="Invalid User: Missing Required Claim"
            if websocket:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=message)
            raise HTTPException(status_code=401, detail=message)

        except jwt.InvalidAudienceError:
            message="Invalid User: Invalid Audience"
            if websocket:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=message)
            raise HTTPException(status_code=401, detail=message)

        except jwt.InvalidIssuerError:
            message="Invalid User: Invalid Issuer"
            if websocket:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=message)
            raise HTTPException(status_code=401, detail=message)

        except jwt.InvalidSignatureError:
            message="Invalid User: Invalid Signature"
            if websocket:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=message)
            raise HTTPException(status_code=401, detail=message)

        except jwt.DecodeError:
            message="Invalid User: Decode Error"
            if websocket:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=message)
            raise HTTPException(status_code=401, detail=message)

        except jwt.InvalidTokenError:
            message="Invalid User: Invalid Token"
            if websocket:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=message)
            raise HTTPException(status_code=401, detail=message)

        except jwt.InvalidKeyError:
            message="Invalid User: Invalid Key"
            if websocket:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=message)
            raise HTTPException(status_code=401, detail=message)

        except Exception as e:
            message ="Invalid User"
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in validating token: Line No: {exc_tb.tb_lineno}")
            if websocket:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=message)
            raise HTTPException(status_code=401, detail=message)

    def get_public_keys(self, unverified_kid_value):
        """
        Function to get public keys
        """
        keys = self.read_json()

        for key in keys:
            if key['kid'] == unverified_kid_value:
                return key
        else:
            keys_json = requests.get(self.public_key_url, timeout=10)
            keys_list = keys_json.json()['keys']
            self.save_keys_to_file(keys_list)
            for key in keys_list:
                if key['kid'] == unverified_kid_value:
                    return key
            else:
                raise HTTPException(status_code=401, detail="Invalid User:Key not found")

    def save_keys_to_file(self, key_list):
        """
        Saves the keys to a JSON file.
        """
        try:
            if not os.path.exists('./Authentication'):
                os.makedirs('./Authentication',exist_ok=True)
            with open('./Authentication/key.json', 'w') as json_file:
                json.dump(key_list, json_file)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error saving keys to file Line No: {exc_tb.tb_lineno}")

    def read_json(self):
        """
        Reads the stored keys JSON file and returns the keys as a list.
        If the file does not exist, returns an empty list.
        """
        try:
            if not os.path.exists('./Authentication/key.json'):
                return []
            with open('./Authentication/key.json', 'r') as json_file:
                return json.load(json_file)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error Opening in the json file Line No: {exc_tb.tb_lineno}")
            return []

    def ensure_bytes(self, key):
        if isinstance(key, str):
            key = key.encode('utf-8')
        return key

    def decode_value(self, value):
        decoded_value = base64.urlsafe_b64decode(self.ensure_bytes(value) + b'==')
        return int.from_bytes(decoded_value, 'big')

    def rsa_pem_from_jwk(self, jwk):
        """
        convert an Azure public key to PEM format
        """
        return RSAPublicNumbers(
            n=self.decode_value(jwk['n']),
            e=self.decode_value(jwk['e'])
        ).public_key(default_backend()).public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
