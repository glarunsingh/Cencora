"""
Module for DB operations
"""
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import os
import sys
import hashlib
import logging
logger = logging.getLogger(__name__)

class DBOPS:
    """
    Main class for DBOPs
    """

    def __init__(self, container_name):
        self.HOST = os.environ['COSMOS_ENDPOINT'] #secret_value.get_secret('COSMOS-ENDPOINT')
        self.MASTER_KEY =  os.environ['COSMOS_KEY'] #secret_value.get_secret('COSMOS-KEY')
        self.DATABASE_ID = os.getenv('COSMOS_NEWS_DATABASE')
        self.CONTAINER_ID = os.getenv(container_name)
        self.client = cosmos_client.CosmosClient(self.HOST,
                                                 {'masterKey': self.MASTER_KEY},
                                                 user_agent="CosmosDBPythonQuickstart",
                                                 user_agent_overwrite=True)

    def create_db(self):
        """
        function to create DB if it not exists
        """
        db_name = self.DATABASE_ID
        try:
            db = self.client.create_database(db_name)
            logger.info('Database with id \'{0}\' created'.format(db_name))
            print('Database with id \'{0}\' created'.format(db_name))
        except exceptions.CosmosResourceExistsError:
            db = self.client.get_database_client(db_name)
            logger.info('Database with id \'{0}\' was found'.format(db_name))
            print('Database with id \'{0}\' was found'.format(db_name))
        return db

    def create_db_container(self):
        """
        function to create a container if it doesn't exist
        """
        container_name = self.CONTAINER_ID
        db = self.create_db()
        try:
            container = db.create_container(id=container_name, partition_key=PartitionKey(path='/source_name'))
            logger.info('Container with id \'{0}\' created'.format(container_name))
            print('Container with id \'{0}\' created'.format(container_name))

        except exceptions.CosmosResourceExistsError:
            container = db.get_container_client(container_name)
            logger.info('Container with id \'{0}\' was found'.format(container_name))
            print('Container with id \'{0}\' was found'.format(container_name))
        return container


class DefinitiveDBOPS(DBOPS):
    """
    Main class for news_data DB operations
    """

    def __init__(self):
        DBOPS.__init__(self, 'COSMOS_NEWS_CONTAINER')

    def create_items(self, json_data):
        """
        function to add items to DB
        """
        container = self.create_db_container()
        logger.info(f'Adding items to DB container {self.CONTAINER_ID}')
        print('\nCreating Items\n')
        for item in json_data:
            item['id'] = hashlib.sha256(item['client_id'].encode('utf-8')).hexdigest()
            container.create_item(body=item)

    def upsert_items(self, json_data):
        """
        function to add/update items in DB
        """
        try:
            container = self.create_db_container()
            logger.info(f"Adding/Updating Items to container {self.CONTAINER_ID}\n")
            print('\nCreating Items\n')
            for item in json_data:
                item['id'] = hashlib.sha256(item['client_id'].encode('utf-8')).hexdigest()
                # item['id']=item['client_id']
                container.upsert_item(body=item)
            logger.info("data uploaded to DB")
            print("data uploaded to DB")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while uploading data."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            print(f"Following exception {e} occurred while uploading data")

    def query_items(self, source_name):
        """
        function to query items from news_data db
        """
        try:
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for given {source_name}\n')
            print(f'\nQuerying from {self.CONTAINER_ID} for given {source_name}\n')
            container = self.create_db_container()
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT * from r where r.source_name = @source_name",
                parameters=[
                    {"name": "@source_name", "value": source_name}
                ],
                enable_cross_partition_query=True
            ))
            logger.info(f"Counts of items extracted: {len(items)}")
            print(len(items))
            return items
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching data from DB."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            print(f"Following exception {e} occurred while fetching data")


class DefinitiveClientDBOPS(DBOPS):
    """
        Main class for news_data DB operations
        """

    def __init__(self):
        DBOPS.__init__(self, 'COSMOS_DEFINITIVE_CLIENT_CONTAINER')

    def query_clients(self):
        """
        function to query clients from definitive_client_information container
        """
        try:
            logger.info(f'\nQuerying from {self.CONTAINER_ID}\n')
            print(f'\nQuerying from {self.CONTAINER_ID}\n')
            container = self.create_db_container()
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.client_name,r.client_id from r",
                enable_cross_partition_query=True
            ))
            logger.info(f"Count of items extracted: {len(items)}")
            print(len(items))
            return items
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching data from DB."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)


class ConfigDetails(DBOPS):
    """
        Main class for config Container operations
        """

    def __init__(self):
        DBOPS.__init__(self, 'COSMOS_CONFIG_CONTAINER')

    def get_config(self, source_name, property_name):
        """
        function to get config details
        """
        try:
            logger.info(f'Querying from {self.CONTAINER_ID}')
            print(f'\nQuerying from {self.CONTAINER_ID}\n')
            container = self.create_db_container()
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query=f"SELECT r.data from r WHERE r.source_name = @source_name and r.property = @property_name",
                parameters=[
                    {"name": "@source_name", "value": source_name},
                    {"name": "@property_name", "value": property_name}
                ],
                enable_cross_partition_query=True
            ))
            logger.info(f"Property extracted: {property_name}")
            return items
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching data from DB."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            print(f"Following exception {e} occurred while fetching data")
