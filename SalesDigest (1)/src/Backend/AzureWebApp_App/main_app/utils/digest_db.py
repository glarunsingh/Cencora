"""
Module for DB operations
"""
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import os
import sys
import hashlib
# from dotenv import load_dotenv
from config.key_vault import key_vault
secret_value = key_vault()

import logging
logger = logging.getLogger(__name__)

class DBOPS:
    """
    Main class for DBOPs
    """

    def __init__(self, container_name):
        self.HOST = secret_value.get_secret('COSMOS-ENDPOINT')
        self.MASTER_KEY = secret_value.get_secret('COSMOS-KEY')
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
        except exceptions.CosmosResourceExistsError:
            db = self.client.get_database_client(db_name)
            logger.info('Database with id \'{0}\' was found'.format(db_name))
        return db

    def create_db_container(self, partition):
        """
        function to create container if it doesn't exist
        """
        container_name = self.CONTAINER_ID
        db = self.create_db()
        try:
            container = db.create_container(id=container_name, partition_key=PartitionKey(path=f'/{partition}'))
            logger.info('Container with id \'{0}\' created'.format(container_name))

        except exceptions.CosmosResourceExistsError:
            container = db.get_container_client(container_name)
            logger.info('Container with id \'{0}\' was found'.format(container_name))
        return container


class DigestDBOPS(DBOPS):
    """
    Main class for news_data DB operations
    """

    def __init__(self):
        DBOPS.__init__(self, 'COSMOS_NEWS_CONTAINER')

    def create_items(self, json_data):
        """
        function to add items to DB
        """
        container = self.create_db_container("source_name")
        logger.info(f'\nCreating Items to container {self.CONTAINER_ID}\n')
        for item in json_data:
            item['id'] = hashlib.sha256(item['news_url'].encode('utf-8')).hexdigest()
            container.create_item(body=item)

    def delete_item(self, source_name):
        container = self.create_db_container("source_name")
        items = list(container.query_items(
            query="SELECT r.id FROM r where r.source_name=@source_name",
            parameters=[
                {"name": "@source_name", "value": source_name}
            ],
            enable_cross_partition_query=True
        ))
        logger.info('\nDeleting Item by Id\n')
        for i in items:
            response = container.delete_item(item=i['id'], partition_key=source_name)

            logger.info('Deleted item\'s Id is {0}'.format(i['id']))

    def upsert_items(self, json_data):
        """
        function to add/update items in DB
        """
        try:
            container = self.create_db_container("source_name")
            logger.info(f"Adding/Updating Items to container {self.CONTAINER_ID}\n")
            for item in json_data:
                item['id'] = hashlib.sha256(item['news_url'].encode('utf-8')).hexdigest()
                container.upsert_item(body=item)
            logger.info("data uploaded to DB")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while uploading data."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)

    def query_url(self, source_name, client_name):
        """
        function to query the existing urls for a particular source and client
        """
        try:
            logger.info(f"Extracting url list for source {source_name}")
            container = self.create_db_container("source_name")
            items = list(container.query_items(
                query="SELECT r.news_url FROM r WHERE r.source_name=@source_name and r.client_name = @client_name",
                parameters=[
                    {"name": "@source_name", "value": source_name},
                    {"name": "@client_name", "value": client_name}
                ],
                enable_cross_partition_query=True
            ))
            url_list = [i['news_url'] for i in items]
            return url_list
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while extracting urls from DB."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

    def query_items(self, source_name, client_name, start_date, end_date, sentiment_list):
        """
        function to query items from news_data db
        """
        try:
            logger.info("Querying the items to get news data from DB")

            placeholder_source_name=[f"@source_name_{i}" for i in range(len(source_name))]
            in_clause_source_name = ','.join(placeholder_source_name)
            source_parameters = [{"name": placeholder_source_name[i], "value": source_name[i]}
                          for i in range(len(source_name))]

            placeholder_client_name = [f"@client_name_{i}" for i in range(len(client_name))]
            in_clause_client_name = ','.join(placeholder_client_name)
            client_parameters = [{"name": placeholder_client_name[i], "value": client_name[i]} for i in
                          range(len(client_name))]

            placeholder_sentiment_name = [f"@sentiment_name_{i}" for i in range(len(sentiment_list))]
            in_clause_sentiment_list = ','.join(placeholder_sentiment_name)
            sentiment_parameters = [{"name": placeholder_sentiment_name[i], "value": sentiment_list[i].lower()} for i in
                          range(len(sentiment_list))]

            container = self.create_db_container("source_name")
            # Including the partition key value of account_number in the WHERE \
            # filter results in a more efficient query
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for given {source_name},{client_name},{sentiment_list}\n')

            #Adding Date parameters
            other_parameters = [
                {"name": "@start_date", "value": start_date},
                {"name": "@end_date", "value": end_date}
            ]
            parameters = source_parameters + client_parameters + sentiment_parameters + other_parameters
            items = list(container.query_items(
                query=f"SELECT r.source_name,r.client_name,r.news_title,r.news_url,r.news_summary,r.news_date,r.sentiment \
                    FROM r WHERE r.source_name in ({in_clause_source_name}) and  r.client_name in ({in_clause_client_name}) and \
                    lower(r.sentiment) in ({in_clause_sentiment_list}) and r.news_date >= @start_date and r.news_date<= @end_date",
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            logger.info(f"Count of items extracted: {len(items)}")
            return items
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching data from DB."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

    def query_def_items(self, source_name, client_name):
        """
        function to query items from news_data db
        """
        try:
            logger.info('Querying for items in database to load to excel')
            container = self.create_db_container("source_name")
            # Including the partition key value of account_number in the WHERE \
            # filter results in a more efficient query
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for given {source_name},{client_name}\n')
            items = list(container.query_items(
                query=f"SELECT * FROM r WHERE r.source_name = @source_name and \
                    r.client_name = @client_name",
                parameters=[
                    {"name": "@source_name", "value": source_name},
                    {"name": "@client_name", "value": client_name}
                ],
                enable_cross_partition_query=True
            ))
            logger.info(f"Count of items extracted: {len(items)}")
            return items
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching data from DB."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

    ############
    def query_definitive_data_excel(self, table_list, source_name, client_name):
        try:
            logger.info('Querying for items in database to load to excel')
            table_list = [items.replace("'", "\\'") for items in table_list]
            source_name = source_name.replace("'", "\\'")
            client_name = client_name.replace("'", "\\'")

            logger.info(f"Client Name to query: {client_name}")
            container = self.create_db_container("source_name")

            placeholder_column_name = [f"@column_name_{i}" for i in range(len(table_list))]
            select_column_name = ",".join([f"r[{col}]" for col in placeholder_column_name])
            column_parameters = [{"name": placeholder_column_name[i], "value": table_list[i]} for i in range(len(table_list))]

            others_parameters = [
                    {"name": "@source_name", "value": source_name},
                    {"name": "@client_name", "value": client_name}
                ]
            parameters = column_parameters + others_parameters

            queryText = f"SELECT {select_column_name} FROM r WHERE r.source_name = @source_name AND r.client_name = @client_name"
            items = list(container.query_items(query=queryText,
                                               parameters= parameters,
                                               enable_cross_partition_query=True
                                               ))

            # changing the column name from $1,$2 to the actual name
            value=items[0]
            for table_name in range(1,len(table_list)+1):
                placeholder=f"${table_name}"
                if placeholder in value.keys():
                    value[table_list[table_name-1]]=value.pop(placeholder)

            logger.info(f"Count of items extracted: {len(items)}")
            return value

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching data from DB."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

    def query_excel_items(self, input_date, source_name, client_name):
        """
        function to extract data from DB export to excel
        """
        try:
            logger.info('Querying for items in database to load to excel')
            placeholder_client_name = [f"@client_name_{i}" for i in range(len(client_name))]
            in_clause_client_name = ','.join(placeholder_client_name)
            client_parameters = [{"name": placeholder_client_name[i], "value": client_name[i]}
                          for i in range(len(client_name))]

            container = self.create_db_container("source_name")
            # Including the partition key value of account_number in the WHERE \
            # filter results in a more efficient query

            placeholder_input_date = [f"@date_{i}" for i in range(len(input_date))]
            query_multidate = " OR ".join([f"STARTSWITH(r.news_date,'{date}')" for date in placeholder_input_date])
            date_parameters = [{"name": placeholder_input_date[i], "value": input_date[i]}
                          for i in range(len(input_date))]


            logger.info(f'\nQuerying from {self.CONTAINER_ID} for given {source_name},{client_name}\n')

            others_parameters = [
                    {"name": "@source_name", "value": source_name}
                ]

            parameters=others_parameters + client_parameters + date_parameters

            items = list(container.query_items(
                query=f"SELECT r.client_name,r.news_title,r.news_url,r.news_summary,r.news_date,r.sentiment \
                    FROM r WHERE r.source_name=@source_name and  r.client_name in ({in_clause_client_name}) and \
                    ({query_multidate})",
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            logger.info(f"Items queried! Container: {self.CONTAINER_ID} ")
            return items

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Failed to extract data from DB.Error querying data- "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def query_breaking_news(self, department, start_date, end_date):
        """
        function to query breaking news from news_data db
        """
        try:
            logger.info('Querying for Breaking News in database')
            client_db = ClientDBOPs()
            client_list = client_db.query_client(department)

            placeholder_client_name = [f"@client_name_{i}" for i in range(len(client_list))]
            in_clause_client_name = ','.join(placeholder_client_name)
            client_parameters = [{"name": placeholder_client_name[i], "value": client_list[i]}
                          for i in range(len(client_list))]

            container = self.create_db_container("source_name")
            others_parameters =[
                    {"name": "@breaking_news", "value": "true"},
                    {"name": "@start_date", "value": start_date},
                    {"name": "@end_date", "value": end_date}
                ]
            # Including the partition key value of account_number in the WHERE \
            # filter results in a more efficient query
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for Breaking News\n')

            parameters=others_parameters + client_parameters
            items = list(container.query_items(
                query=f"SELECT r.source_name,r.client_name,r.news_title,r.news_url,r.news_summary,r.news_date,r.sentiment \
                    FROM r WHERE r.breaking_news=@breaking_news and r.client_name in ({in_clause_client_name}) and\
                        r.news_date >= @start_date and r.news_date<= @end_date",
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            items = sorted(items, key=lambda x: x['news_date'], reverse=True)
            logger.info(f"Count of items extracted: {len(items)}")
            return items
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching breaking news from DB."
                         f" Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

    def query_items_from_url_list(self,url_list,client_list,source_list):
        """
        Function to query items from url list for keyword search excel generation
        """
        try:

            container = self.create_db_container("source_name")
            logger.info(f'\nQuerying data to create excel for keyword search from  {self.CONTAINER_ID} \n')

            # Adding empty string to client_list so that non-client news sources can be included
            client_list += [""]

            placeholder_url_name = [f"@url_name_{i}" for i in range(len(url_list))]
            in_clause_url_name = ','.join(placeholder_url_name)
            url_parameters = [{"name": placeholder_url_name[i], "value": url_list[i]}
                                 for i in range(len(url_list))]

            placeholder_client_name = [f"@client_name_{i}" for i in range(len(client_list))]
            in_clause_client_name = ','.join(placeholder_client_name)
            client_parameters = [{"name": placeholder_client_name[i], "value": client_list[i]}
                                 for i in range(len(client_list))]

            placeholder_source_name = [f"@source_name_{i}" for i in range(len(source_list))]
            in_clause_source_name = ','.join(placeholder_source_name)
            source_parameters = [{"name": placeholder_source_name[i], "value": source_list[i]}
                                 for i in range(len(source_list))]


            parameters = url_parameters + client_parameters + source_parameters
            items = list(container.query_items(
                query=f"SELECT r.source_name,r.client_name,r.news_title,r.news_url,r.news_summary,r.news_date,"
                      f"r.sentiment FROM r WHERE r.news_url IN ({in_clause_url_name}) AND r.client_name"
                      f" IN ({in_clause_client_name}) AND r.source_name IN ({in_clause_source_name}) ",
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            logger.info(f"Excel data queried! Container: {self.CONTAINER_ID} ")
            return items

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Failed to extract data from DB using url list. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception



class KeywordDBOPs(DBOPS):
    """
    Main class for keyword DB operations
    """

    def __init__(self):
        """
        init function for Keyword db
        """
        DBOPS.__init__(self, 'COSMOS_KEY_CONTAINER')

    def query_keyword_list(self, department_name):
        """
        function to get the list of keywords based on department
        """
        try:
            container = self.create_db_container("department_name")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.keyword_name FROM r WHERE r.department_name=@department_name ORDER BY r.count DESC",
                parameters=[
                    {"name": "@department_name", "value": department_name}
                ],
                enable_cross_partition_query=True
            ))
            k_list = [i['keyword_name'] for i in items]
            return k_list
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching keywords. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

    def query_admin_table(self, department_name):
        """
        function to get the admin table for keywords
        """
        try:
            container = self.create_db_container("department_name")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.id AS keyword_uuid,r.keyword_name,r.department_name,r.last_updated_on,r.last_updated_by"
                      " FROM r WHERE r.department_name=@department_name",
                parameters=[
                    {"name": "@department_name", "value": department_name}
                ],
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching keywords for admins. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception

    def increment_keyword_count(self, keyword_name,department_name):
        """
        Function to increment the keyword count in the database
        """
        try:
            # removing white spaces and lower casing the keyword
            keyword_name = keyword_name.lower()
            keyword_name = keyword_name.strip()
            container = self.create_db_container("department_name")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {keyword_name}\n')

            # Checking if the keyword exists in the database
            items = list(container.query_items(
                query="SELECT * FROM r WHERE lower(r.keyword_name)=@keyword_name and r.department_name=@department_name",
                parameters=[
                    {"name": "@keyword_name", "value": keyword_name},
                    {"name": "@department_name", "value": department_name}
                ],
                enable_cross_partition_query=True
            ))
            if items:
                item = items[0]
                item['count'] = item['count'] + 1
                container.upsert_item(item)
                logger.info(f"Keyword '{keyword_name}' count updated in the database")
            else:
                logger.info(f"Keyword '{keyword_name}' not found in the database.Hence no need to update")

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while incrementing keywords counts "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)


class UserDBOPs(DBOPS):
    """
    Main class for User DB operations
    """

    def __init__(self):
        """
        init function for Keyword db
        """
        DBOPS.__init__(self, 'COSMOS_USER_CONTAINER')

    def query_fav_client(self, email_id):
        """
        function to get the list of fav clients
        """
        try:
            container = self.create_db_container("email_id")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {email_id}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.favourite_client_list FROM r WHERE r.email_id=@email_id",
                parameters=[
                    {"name": "@email_id", "value": email_id}
                ],
                enable_cross_partition_query=True
            ))
            if not items:
                raise Exception
            fav_list = [i['favourite_client_list'] for i in items]
            
            logger.info(f"fav_list: - {fav_list}")
            return fav_list
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching favorite clients. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return [[]]

    def query_fav_client_and_email_status(self, email_id):
        """
        function to get the list of fav clients and email status of user
        """
        try:
            container = self.create_db_container("email_id")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {email_id}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.favourite_client_list, r.email_notify FROM r WHERE r.email_id=@email_id",
                parameters=[
                    {"name": "@email_id", "value": email_id}
                ],
                enable_cross_partition_query=True
            ))
            if not items:
                raise Exception
            fav_list = [i['favourite_client_list'] for i in items]
            email_notify = items[0]['email_notify']

            logger.info(f"fav_list: - {fav_list}")
            return fav_list,email_notify
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching favorite clients. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return [[]],False


class ClientDBOPs(DBOPS):
    """
    Main class for Client DB operations
    """

    def __init__(self):
        """
        init function for Keyword db
        """
        DBOPS.__init__(self, 'COSMOS_CLIENT_CONTAINER')

    def query_client(self, department_name):
        """
        function to get the list of clients
        """
        try:
            container = self.create_db_container("department_name")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.client_name FROM r WHERE r.department_name=@department_name",
                parameters=[
                    {"name": "@department_name", "value": department_name}
                ],
                enable_cross_partition_query=True
            ))
            client_list = [i['client_name'] for i in items]
            logger.info(f"client_list:- {client_list}")
            return client_list
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching clients. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

    def query_client_synonyms(self, department_name):
        """
        function to get the list of clients
        """
        try:
            container = self.create_db_container("department_name")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.client_name, r.synonyms FROM r WHERE r.department_name=@department_name",
                parameters=[
                    {"name": "@department_name", "value": department_name}
                ],
                enable_cross_partition_query=True
            ))
            logger.info(f"client_list:- {items}")
            return items
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching clients and synonymns. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

    def query_admin_table(self, department_name):
        """
        function to get the admin table
        """
        try:
            container = self.create_db_container("department_name")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.id AS client_uuid,r.client_name,r.department_name,r.synonyms,r.last_updated_on,r.last_updated_by"
                      " FROM r WHERE r.department_name=@department_name",
                parameters=[
                    {"name": "@department_name", "value": department_name}
                ],
                enable_cross_partition_query=True
            ))
            logger.info(f"client_list:- {items}")
            return items
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching admin table details from the database. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            raise Exception


class SourceDBOPs(DBOPS):
    """
    Main class for Client DB operations
    """

    def __init__(self):
        """
        init function for Keyword db
        """
        DBOPS.__init__(self, 'COSMOS_SOURCE_CONTAINER')

    def query_source(self, department_name, client_specific):
        """
        function to get the list of sources based on client/non client
        """
        try:
            container = self.create_db_container("department")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.name FROM r WHERE r.department=@department_name and r.client_specific=@client_specific",
                parameters=[
                    {"name": "@department_name", "value": department_name},
                    {"name": "@client_specific", "value": client_specific}
                ],
                enable_cross_partition_query=True
            ))
            return items

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching source list. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

    def query_source_for_department(self, department_name):
        """
        function to get the list of source based on department
        """
        try:
            container = self.create_db_container("department")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.name FROM r WHERE r.department=@department_name",
                parameters=[
                    {"name": "@department_name", "value": department_name}
                ],
                enable_cross_partition_query=True
            ))
            source_list = [i['name'] for i in items]
            return source_list

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching source list. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []


class DefinitiveClientDBOPS(DBOPS):
    """
        Main class for Definitive Client DB operations
        """

    def __init__(self):
        """
        init function for Keyword db
        """
        DBOPS.__init__(self, 'COSMOS_DEFINITIVE_CLIENT_CONTAINER')

    def query_client(self, department_name, source_name):
        """
        function to get the list of clients
        """
        try:
            container = self.create_db_container("source_name")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {department_name}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
                query="SELECT r.client_name FROM r WHERE r.department_name=@department_name AND"
                      " r.source_name=@source_name",
                parameters=[
                    {"name": "@department_name", "value": department_name},
                    {"name": "@source_name", "value": source_name}
                ],
                enable_cross_partition_query=True
            ))
            client_list = [i['client_name'] for i in items]
            logger.info(f"client_list:- {client_list}")
            return client_list
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching clients. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)
            return []

class ConfigDBOPS(DBOPS):
    """
        Main class for Config operations
        """

    def __init__(self):
        """
        init function for Keyword db
        """
        DBOPS.__init__(self, 'COSMOS_CONFIG_CONTAINER')

    def query_prompt(self, source_name, prompt_name):
        """
        function to get the list of clients
        """
        try:
            container = self.create_db_container("source_name")
            logger.info(f'\nQuerying from {self.CONTAINER_ID} for {prompt_name}\n')
            # Including the partition key value of account_number in the WHERE filter results in a more efficient query
            items = list(container.query_items(
               query="SELECT r.prompt FROM r WHERE r.source_name=@source_name and r.prompt_name=@prompt_name",
                parameters=[
                    {"name":"@source_name","value":source_name},
                    {"name":"@prompt_name","value":prompt_name}
                ],
                enable_cross_partition_query=True
            ))[0]
            prompt =items['prompt']
            logger.info(f"Querying from {self.CONTAINER_ID} for {prompt_name}\n Completed'")
            return prompt
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error(f"Exception occurred while fetching prompt {prompt_name}. "
                         f"Line No: {exc_tb.tb_lineno}  Error: {str(e)}", stack_info=True)