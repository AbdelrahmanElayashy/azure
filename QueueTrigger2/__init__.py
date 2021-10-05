import json
import logging
import urllib.parse as urlparse
import azure.functions as func
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity
import logging
import threading
from .tableStorage import _tableStorage
from azure.cosmosdb.table.tablebatch import TableBatch
from azure.keyvault.keys import KeyClient
from azure.identity import DefaultAzureCredential
import random
from time import sleep
from azure.appconfiguration import AzureAppConfigurationClient
import os


def get_blob_meta(msg):
    url = json.loads(msg.get_body().decode(
        'utf-8').replace("'", "\""))['data']['url']
    parsed_url = urlparse.urlparse(url)
    return {
        "storage": parsed_url.netloc.split('.')[0],
        "container": parsed_url.path.split('/')[1],
        "folder": parsed_url.path.split('/')[2],
        "blob": parsed_url.path.split('/')[3]
    }


def create_product_entity(partition_key, row_key, count, image_table):
    entity = Entity()
    entity.PartitionKey = partition_key
    entity.RowKey = row_key
    entity.ImageTable = image_table
    entity.Count = count
    return entity


def create_image_entity(partition_key, row_key, image_name):
    entity = Entity()
    entity.PartitionKey = partition_key
    entity.RowKey = row_key
    entity.ImageName = image_name
    return entity


def main(msg: func.QueueMessage) -> None:

    conn = os.environ['AzureWebJobsStorage']

    blob_meta = get_blob_meta(msg)
    client_table = blob_meta['container']
    client_product = blob_meta['folder']
    image_name = blob_meta['blob']
    image_id = image_name.split("_")[3]
    client_image_table = "image{}".format(client_table)

    table_service = TableService(
        account_name=blob_meta['storage'], connection_string=conn)

    if(not table_service.exists(client_table)):
        table_service.create_table(client_table)
        table_service.create_table(client_image_table)

    try:
        # if entity does not exist, then throw and insert it
        table_service.get_entity(client_table, client_table, client_product)
    except:
        count = 0
        entity_product = create_product_entity(
            client_table, client_product, count, client_image_table)
        table_service.insert_or_replace_entity(client_table, entity_product)

    header_etag = "random-etag"
    response_etag = "random-response"
    while True:
        sleep(random.random())  # sleep between 0 and 1 second.
        header = table_service.get_entity(
            client_table, client_table, client_product)
        header_etag = header['etag']
        new_count = header['Count'] + 1
        entity_product = create_product_entity(
            client_table, client_product, new_count, client_image_table)
        try:
            response_etag = table_service.merge_entity(client_table, entity_product,
                                                       if_match=header_etag)
            break
        except:
            logging.info("race condition detected")

    entity_img = create_image_entity(client_product, image_id, image_name)
    table_service.insert_or_replace_entity(client_image_table, entity_img)
