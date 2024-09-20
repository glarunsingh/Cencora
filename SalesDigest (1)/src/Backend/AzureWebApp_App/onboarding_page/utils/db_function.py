import hashlib
import logging
import os
import sys

from azure.cosmos import CosmosClient as cs

logger = logging.getLogger(__name__)

from config.key_vault import key_vault
secret_value = key_vault()


class DBOPS:
    def __init__(self):
        """
        Class for interacting with a CosmosDB database.
        """
        try:
            self.URL = secret_value.get_secret('COSMOS-ENDPOINT')
            self.KEY = secret_value.get_secret('COSMOS-KEY')
            self.DATABASE_NAME = os.environ['COSMOS_NEWS_DATABASE']
            self.NEWS_CONTAINER_NAME = os.environ['COSMOS_NEWS_CONTAINER']
            self.KEY_CONTAINER_NAME = os.environ['COSMOS_KEY_CONTAINER']
            self.CLIENT_INF_CONTAINER_NAME = os.environ['COSMOS_CLIENT_CONTAINER']
            self.USER_DATA_CONTAINER = os.environ['COSMOS_USER_CONTAINER']
            self.read_client = cs(self.URL, credential=self.KEY)
            self.database = self.read_client.get_database_client(self.DATABASE_NAME)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    @staticmethod
    def sha_conversion(data: str) -> str:
        sha256 = hashlib.sha256(data.encode('utf-8')).hexdigest()
        return sha256

    def query_items(self, query, container_name, cross_partition=True,parameters=None):
        """
        query the items from the database
        """
        try:
            container = self.database.get_container_client(container_name)
            results = list(container.query_items(query=query,
                                                 parameters=parameters,
                                                 enable_cross_partition_query=cross_partition))
            return results

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def upsert_items(self, data, container_name):
        """
        update/insert the items in the database
        """
        try:
            container = self.database.get_container_client(container_name)
            container.upsert_item(data)
            logger.info(f"Data uploaded to Container:{container_name}")

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def delete_items(self, item_id, partition_key, container_name):
        """
        delete items from the database
        """
        try:
            container = self.database.get_container_client(container_name)
            container.delete_item(item=item_id, partition_key=partition_key)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def get_department_name(self):
        """
        get the list of the departments
        """
        try:
            query = "SELECT DISTINCT(c.department_name) FROM c"
            results = self.query_items(query, self.CLIENT_INF_CONTAINER_NAME)
            final_result = [item['department_name'] for item in results]
            return final_result

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def get_clients_name(self, department_name):
        """
        Retrieves a list of client names for a given department name.
        """
        try:
            query = f"SELECT c.client_name FROM c WHERE c.department_name=@department_name"
            parameter=[{"name": "@department_name", "value": department_name}]
            results = self.query_items(query, self.CLIENT_INF_CONTAINER_NAME, cross_partition=False,
                                       parameters=parameter)
            final_result = [item['client_name'] for item in results]
            return final_result

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def update_client_data(self, details):
        """
            This function updates client data in the USER_DATA_CONTAINER.
        """
        try:
            item = {
                'id': self.sha_conversion(details.email_id),
                'emp_id': details.emp_id,
                'first_name': details.first_name,
                'last_name': details.last_name,
                'email_id': details.email_id,
                'favourite_client_list': details.favourite_client_list,
                'email_notify': details.email_notify,
                'department_name': details.department_name
            }
            self.upsert_items(item, self.USER_DATA_CONTAINER)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def get_user_details(self, emp_id):
        """
            This function retrieves user details from the database based on the provided employee ID.
        """
        try:
            query = f"SELECT * FROM c WHERE c.emp_id=@emp_id"
            parameter=[{"name": "@emp_id", "value": emp_id}]
            results = self.query_items(query, self.USER_DATA_CONTAINER, cross_partition=True,
                                       parameters=parameter)
            if results:
                return results[0]
            else:
                return []
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def update_user_details_based_on_token(self,user_detail,token_details):
        """
        function to update client details if the department name is change in the Azure Ad access token
        """
        try:
            user_detail['department_name'] = token_details['department_name']
            user_detail['first_name'] = token_details['first_name']
            user_detail['last_name'] = token_details['last_name']
            user_detail['favourite_client_list'] = []
            self.upsert_items(user_detail, self.USER_DATA_CONTAINER)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception


    # def get_client_id(self, client_name, department_name):
    #     """
    #     Get the client ID based on the client name and department name.
    #     """
    #     try:
    #         # Escape single quotes in client and department names
    #         client_name = client_name.replace("'", "\\'")
    #         department_name = department_name.replace("'", "\\'")
    #
    #         # Construct the query to retrieve the client ID
    #         query = f"SELECT c.id FROM c WHERE c.client_name='{client_name}' AND c.department_name='{department_name}'"
    #
    #         # Query the items to get the client ID
    #         results = self.query_items(query, self.CLIENT_INF_CONTAINER_NAME, cross_partition=False)
    #
    #         # Return the client ID
    #         return results[0]['id']
    #     except Exception as e:
    #         exc_type, exc_obj, exc_tb = sys.exc_info()
    #         logger.error(f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
    #         raise Exception
