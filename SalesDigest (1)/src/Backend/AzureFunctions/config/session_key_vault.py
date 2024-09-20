import os
import sys

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

import logging
logger = logging.getLogger(__name__)

value_list = ["PROD_BING_PLUGIN_KEY", "AZURE_OPENAI_API_ENDPOINT_WEBTOOLS", "AZURE_OPENAI_API_KEY",
              "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "BING_NEWS_PlUGIN_URL", "BING_NEWS_KEY",
              "BING_NEWS_URL", "BING_SEARCH_URL", "COSMOS_ENDPOINT", "COSMOS_KEY", "DEFINITIVE_PASSWORD",
              "DEFINITIVE_URL", "DEFINITIVE_USERNAME", "EMBEDDINGS_API_KEY", "EMBEDDINGS_DEPLOYMENT",
              "EMBEDDINGS_ENDPOINT", "EMBEDDINGS_MODEL", "SCRAPE_PLUGIN_URL",
              "APPLICATION-INSIGHTS-STRING-TIMER","APPLICATION-INSIGHTS-STRING-WEBAPP",
              "AZURE_AI_SEARCH_API_KEY","AZURE_AI_SEARCH_ENDPOINT"]


def get_all_values():
    try:
        if not os.getenv("IS_KEY_VAULT_VALUES_CONFIGURED"):
            credential = DefaultAzureCredential()
            keyVaultName = os.getenv("KEY_VAULT_NAME")
            KVUri = f"https://{keyVaultName}.vault.azure.net"
            client = SecretClient(vault_url=KVUri, credential=credential)
            os.environ["IS_KEY_VAULT_VALUES_CONFIGURED"] = "True"
            for secret_name in value_list:
                secret_key_name = secret_name.replace("_", "-")
                secret_value = client.get_secret(secret_key_name).value
                os.environ[secret_name] = secret_value
                if not secret_value:
                    raise Exception
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error(f"Unable to retrieve the keys: "
                   f"{exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)


if __name__ == "__main__":
    get_all_values()
