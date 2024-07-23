"""
Module for DB operations
"""
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import os
import sys
import logging
import hashlib
from dotenv import load_dotenv
from BeckerHospital.utils.logs import create_log
logger = create_log(name="Becker_Hospital", level=logging.info)
_= load_dotenv("./BeckerHospital/config/db.env")

class DBOPS:
    """
    Main class for DBOPs
    """
    def __init__(self,container_name):
        self.HOST = os.getenv('COSMOS_ENDPOINT')
        self.MASTER_KEY = os.getenv('COSMOS_KEY')
        self.DATABASE_ID = os.getenv('COSMOS_NEWS_DATABASE')
        self.CONTAINER_ID = os.getenv(container_name)
        self.client = cosmos_client.CosmosClient(self.HOST,
                                                 {'masterKey': self.MASTER_KEY},
                                                 user_agent="CosmosDBPythonQuickstart",
                                                 user_agent_overwrite=True)
        
    def create_db(self):
        '''
        function to create DB if it not exists
        '''
        db_name=self.DATABASE_ID
        try:
            db = self.client.create_database(db_name)
            logger.info('Database with id \'{0}\' created'.format(db_name))
            print('Database with id \'{0}\' created'.format(db_name))
        except exceptions.CosmosResourceExistsError:
            db = self.client.get_database_client(db_name)
            logger.info('Database with id \'{0}\' was found'.format(db_name))
            print('Database with id \'{0}\' was found'.format(db_name))
        return db
    
    def create_db_container(self,partition_name):
        '''
        function to create conatiner if it doesn't exists
        '''
        container_name=self.CONTAINER_ID
        db = self.create_db()
        try:
            container = db.create_container(id=container_name, partition_key=PartitionKey(path=f'/{partition_name}'))
            logger.info('Container with id \'{0}\' created'.format(container_name))
            print('Container with id \'{0}\' created'.format(container_name))

        except exceptions.CosmosResourceExistsError:
            container = db.get_container_client(container_name)
            logger.info('Container with id \'{0}\' was found'.format(container_name))
            print('Container with id \'{0}\' was found'.format(container_name))
        return container

class BeckerDBOPS(DBOPS):
    """
    Main class for news_data DB operations
    """
    def __init__(self):
        DBOPS.__init__(self,'COSMOS_NEWS_CONTAINER')

    def create_items(self,json_data):
        '''
        function to add items to DB
        '''
        container = self.create_db_container("source_name")
        logger.info(f'\nCreating Items to container {self.CONTAINER_ID}\n')
        print('\nCreating Items\n')
        for item in json_data:
            item['id']=hashlib.sha256(item['news_url'].encode('utf-8')).hexdigest()
            container.create_item(body=item)

    def upsert_items(self,json_data):
        '''
        function to add/update items in DB
        '''
        try:
            container = self.create_db_container("source_name")
            logger.info(f"Adding/Updating Items to container {self.CONTAINER_ID}\n")
            print('\nCreating Items\n')
            for item in json_data:
                item['id']=hashlib.sha256(item['news_url'].encode('utf-8')).hexdigest()
                container.upsert_item(body=item)
            logger.info("data uploaded to DB")
            print("data uploaded to DB")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occured while uploading data."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            print(f"Following exception {e} occured while uploading data")

    def query_url(self,source_name,client_name):
        '''
        function to query the existing urls for a particular source and client
        '''
        try:
            logger.info(f"Extracting url list for source {source_name}")
            print(f"Extracting url list for source {source_name}")
            container = self.create_db_container("source_name")
            items = list(container.query_items(
                query="SELECT r.news_url FROM r WHERE r.source_name=@source_name and r.client_name = @client_name",
                parameters=[
                    { "name":"@source_name", "value": source_name },
                    {"name":"@client_name","value":client_name}
                ],
                enable_cross_partition_query=True
            ))
            url_list = [i['news_url'] for i in items]
            return url_list
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occured while extracting urls from DB."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            print(f"Following exception {e} occured while extracting urls")
            return []

    def query_items(self,source_name,client_name,start_date,end_date):
        '''
        function to query items from news_data db
        '''
        try:
            logger.info('Querying for items in database to load to excel')
            client_name = str(client_name)
            client_name = client_name.replace("[","(")
            client_name = client_name.replace("]",")")

            print(f"cleint_name: {client_name}")
            container = self.create_db_container("source_name")
            # Including the partition key value of account_number in the WHERE \
            # filter results in a more efficient query
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for given {source_name},{client_name}\n')
            print(f'\nQuerying from {self.CONTAINER_ID} for given {source_name},{client_name}\n')
            items = list(container.query_items(
                query=f"SELECT r.client_name,r.news_title,r.news_url,r.news_summary,r.news_date,r.sentiment \
                    FROM r WHERE r.source_name=@source_name and  r.client_name in {client_name} and \
                        r.news_date >= @start_date and r.news_date<= @end_date",
                parameters=[
                    { "name":"@source_name", "value": source_name },
                    { "name":"@client_name", "value": client_name },
                    {"name":"@start_date","value":start_date},
                    {"name":"@end_date","value":end_date}
                ],
                enable_cross_partition_query=True
            ))
            logger.info(f"Count of items extracted: {len(items)}")
            print(len(items))
            return items
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occured while fetching data from DB."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            print(f"Following exception {e} occured while fetching data")
            return []

    def query_excel_items(self,input_date,source_name,client_name):
        '''
        function to extract data from DB export to excel
        '''
        try:
            logger.info('Querying for items in database to load to excel')
            client_name = str(client_name)
            client_name=client_name.replace("[","(")
            client_name=client_name.replace("]",")")

            print(f"cleint_name: {client_name}")
            container = self.create_db_container("source_name")
            # Including the partition key value of account_number in the WHERE \
            # filter results in a more efficient query
            query_multidate = " OR ".join([f"STARTSWITH(r.news_date,'{date}')" for date in input_date])
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for given {source_name},{client_name}\n')
            print(f'\nQuerying from {self.CONTAINER_ID} for given {source_name},{client_name}\n')
            items = list(container.query_items(
                query=f"SELECT r.client_name,r.news_title,r.news_url,r.news_summary,r.news_date,r.sentiment \
                    FROM r WHERE r.source_name=@source_name and  r.client_name in {client_name} and \
                    ({query_multidate})",
                parameters=[
                    { "name":"@source_name", "value": source_name }
                ],
                enable_cross_partition_query=True
            ))

            logger.info(f"Items queried! Container: {self.CONTAINER_ID} ")
            print(items)
            return items

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Failed to extract data from DB.Error querying data- "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

class KeywordDBOPs(DBOPS):
    '''
    Main class for keyword DB operations
    '''
    def __init__(self):
        '''
        init function for Keyword db
        '''
        DBOPS.__init__(self,'COSMOS_KEY_CONTAINER')

    def query_keyword_list(self,department_name):
        """
        function to get the list of keywords based on department
        """
        try:
            container = self.create_db_container("department_name")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            print(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.keyword_name FROM r WHERE r.department_name=@department_name",
                parameters=[
                    {"name":"@department_name","value":department_name}
                ],
                enable_cross_partition_query=True
            ))
            k_list = [i['keyword_name'] for i in items]
            return k_list
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occured while fetching keywords. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            print(f"Following exception {e} occured while fetching keywords")
            return []
    
class ClientDBOPs(DBOPS):
    '''
    Main class for Client DB operations
    '''
    def __init__(self):
        '''
        init function for Keyword db
        '''
        DBOPS.__init__(self,'COSMOS_CLIENT_CONTAINER')

    def query_client(self,department_name):
        """
        function to get the list of clients
        """
        try:
            container = self.create_db_container("department_name")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            print(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.client_name FROM r WHERE r.department_name=@department_name",
                parameters=[
                    {"name":"@department_name","value":department_name}
                ],
                enable_cross_partition_query=True
            ))
            client_list = [i['client_name'] for i in items]
            #print(f"client_list:- {client_list}")
            return client_list
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occured while fetching clients. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            print(f"Following exception {e} occured while fetching clients")
            return []
