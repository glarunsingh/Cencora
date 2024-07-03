#https://github.com/RekhuGopal/PythonHacks/blob/main/Azure_CosmosDB_Python/cosmosdb_crud.py
#https://github.com/Azure-Samples/azure-cosmos-db-python-getting-started/blob/main/cosmos_get_started.py
import os
from azure.cosmos.aio import CosmosClient 
from azure.cosmos import  exceptions, PartitionKey
import json
import asyncio

COSMO_URL = "https://cosmos-keyaccount-qa.documents.azure.com:443/"
COSMO_KEY = "k9LU5BuD46E3pkmWhnsj5xxiRMUWgGT8Psb1XzdRkrHVLlirB1kNJDHf3SBL1aHxTfgn44u21we6ACDbtAUd1Q=="
client = CosmosClient(COSMO_URL, credential=COSMO_KEY)
DATABASE_NAME = 'SalesDigest'
#database = client.get_database_client(DATABASE_NAME)
CONTAINER_NAME = 'News'
#container = database.get_container_client(CONTAINER_NAME)


async def get_or_create_db(client,database_name):
    try:
        database_obj  = client.get_database_client(database_name)
        await database_obj.read()
        return database_obj
    except exceptions.CosmosResourceNotFoundError:
        print("Creating database")
        return await client.create_database(database_name)

async def get_or_create_container(database_obj, container_name):
    try:        
        items_container = database_obj.get_container_client(container_name)
        await items_container.read()   
        return items_container
    except exceptions.CosmosResourceNotFoundError:
        print("Creating container with Client as partition key")
        return await database_obj.create_container(
            id=container_name,
            partition_key=PartitionKey(path="/client"),
            offer_throughput=400)
    except exceptions.CosmosHttpResponseError:
        raise

async def add_news_item(news_items):
    database_obj = await get_or_create_db(client,database_name=DATABASE_NAME)
    container_obj = await get_or_create_container(database_obj,container_name=CONTAINER_NAME)  
    # <create_item>
    for news in news_items:
        await container_obj.create_item(body=news)
        print(f"News item added to container.")
    await client.close()

news_item_example =[
{'id':'1',
  'url': 'https://www.beckershospitalreview.com/finance/hca-shares-continue-climb-to-new-highs.html',
  'source': 'Bing News API',
  'client': 'HCA Healthcare',
  'title': '<b>HCA</b> shares continue climb to new highs',
  'date': '2024-06-06T13:57:00.0000000Z',
  'description': 'Nashville, Tenn.-based HCA operates 186 hospitals and 49,588 total licensed beds. In January, its stock price hit an all-time high, soaring past $300 per share following an 8% increase in revenue in 2023. The stock has maintained momentum, hitting $336.91 on June 5 — a year-over-year increase of approximately 24%.',
  'summary': "HCA Healthcare's stock has seen significant growth, reaching $336.91 per share, a 24% increase year-over-year. This rise has positively impacted the net worth of co-founder Thomas Frist Jr., MD, whose wealth is estimated at $29.7 billion by Bloomberg and $26.2 billion by Forbes. The company's revenue growth is attributed to broad-based volume growth and a recovery in surgical procedures as staffing levels improve.",
  'news': "As HCA Healthcare shares continue their ascent, so too does the estimated net worth of co-founder Thomas Frist Jr., MD. Nashville, Tenn.-based HCA operates 186 hospitals and 49,588 total licensed beds. In January, its stock price hit an all-time high, soaring past $300 per share following an 8% increase in revenue in 2023. The stock has maintained momentum, hitting $336.91 on June 5 — a year-over-year increase of approximately 24%. In comparison, Dallas-based Tenet Healthcare's stock is around $135 per share, while King of Prussia, Pa.-based Universal Health Services' stock stands at about $189 per share. In April, with the release of HCA's first quarter results, CEO Sam Hazen attributed the system's 11.2% year-over-year increase in revenue to 'broad-based volume growth.' The system made headlines with Reuters for its projected recovery in surgical procedures, expected to persist throughout the year as staffing approaches pre-pandemic levels. and, in turn, bolster both bed and surgical capacity. HCA's climb is uplifting news for Dr. Frist Jr., who co-founded the company with his father, Thomas Frist Sr., MD, and entrepreneur Jack Massey in 1968. Dr. Frist Jr. owns more than 20% of the enterprise. The major shareholder has seen his estimated net worth reach new heights in 2024. The Bloomberg Billionaires Index puts Dr. Frist Jr.'s estimated net worth at $29.7 billion at the time of publication, up by about 24% or $5.7 billion year over year. Forbes puts Dr. Frist's wealth at $20.2 billion in 2023 and $26.2 billion today, up nearly 30% year over year and by one billion since February. (The two outlets use different methodologies to arrive at their estimates.)"},
 {
  'id':'2',
  'url': 'https://www.beckershospitalreview.com/hospital-executive-moves/ceo-named-for-2-oregon-hospitals.html',
  'source': 'Bing News API',
  'client': 'HCA Healthcare',
  'title': 'CEO named for 2 Oregon hospitals',
  'date': '2024-06-06T17:48:00.0000000Z',
  'description': 'Brandon Mencini was named CEO of Rogue Regional Medical Center in Medford, Ore., and Ashland (Ore.) Community Hospital. Mr. Mencini brings more than two decades of healthcare executive leadership experience to the role,',
  'summary': 'Brandon Mencini has been appointed CEO of Rogue Regional Medical Center and Ashland Community Hospital in Oregon. He brings over 20 years of healthcare executive experience, having previously served as CEO of Mercy Hospital in Durango, Colorado, and COO of Chippenham Hospital in Richmond, Virginia.',
  'news': "Brandon Mencini was named CEO of Rogue Regional Medical Center in Medford, Ore., and Ashland (Ore.) Community Hospital. Mr. Mencini brings more than two decades of healthcare executive leadership experience to the role, according to a June 5 health system news release. Most recently, he served as CEO of CommonSpirit Health's Mercy Hospital in Durango, Colo. He also previously served as COO of Chippenham Hospital, a 466-bed level 1 trauma and burn center in Richmond, Va., and part of Nashville, Tenn.-based HCA Healthcare, according to the release. Rogue Regional Medical Center and Ashland Community Hospital are part of Medford-based Asante."}
 ]


async def query_items(container_obj, query_text):

    results = container_obj.query_items(
        query=query_text
    )
    item_list = []
    async for item in results:
        item_list.append(item)
    await client.close()
    return item_list

async def main():
    database_obj = await get_or_create_db(client,database_name=DATABASE_NAME)
    container_obj = await get_or_create_container(database_obj,container_name=CONTAINER_NAME)  
    query = "SELECT * FROM News c WHERE c.client IN ('HCA Healthcare')"
    items = await query_items(container_obj, query)
    print(items)
    await client.close()
    
    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    #loop.run_until_complete(add_news_item(news_item_example))
    loop.run_until_complete(main())

'''
async def create_database():
    async with CosmosClient(COSMO_URL, credential=COSMO_KEY) as client:
        try:
            await client.create_database(DATABASE_NAME)
        except exceptions.CosmosResourceExistsError:
            pass
                
async def create_container():
    database = client.get_database_client(DATABASE_NAME)
    try:
        await database.create_container(id=CONTAINER_NAME, partition_key=PartitionKey(path="/id"))
    except exceptions.CosmosResourceExistsError:
        pass
    
async def main():
    database_obj = await get_or_create_db(client,database_name=DATABASE_NAME)
    await get_or_create_container(database_obj, container_name=CONTAINER_NAME)
    print(f"Database '{DATABASE_NAME}' and container '{CONTAINER_NAME}' are ready.")
    await client.close()
'''