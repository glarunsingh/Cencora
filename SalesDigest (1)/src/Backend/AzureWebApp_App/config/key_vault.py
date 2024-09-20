import os
import sys

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

import logging
logger = logging.getLogger(__name__)

class key_vault:
    """
        class to connect to key vault and get the values
    """
    def __init__(self):
        try:
            self.credential = DefaultAzureCredential()
            self.keyVaultName = os.getenv("KEY_VAULT_NAME")
            self.KVUri = f"https://{self.keyVaultName}.vault.azure.net"
            self.client = SecretClient(vault_url=self.KVUri, credential=self.credential)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in connecting to key vault :Line No {exc_tb.tb_lineno}",
                         stack_info=True)
            raise Exception
    def get_secret(self, secret_name):
        """
       This method retrieves a secret from the Azure Key Vault.

       Args:
           secret_name (str): The name of the secret to retrieve.

       Returns:
           str: The value of the secret.
       """
        try:
            # Added so that the secret name not dependent on the key vault name formatting
            secret_name=secret_name.replace("_","-")
            return self.client.get_secret(secret_name).value
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Error in connecting to key vault: {secret_name}: {exc_tb.tb_lineno}  Error: {str(e)}",
                         stack_info=True)
            raise Exception
