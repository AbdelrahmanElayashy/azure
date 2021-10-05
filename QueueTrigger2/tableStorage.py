import logging
import azure.functions as func
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity


class _tableStorage:
    def __init__(self, account, key):
        self.table_service = TableService(account, key)

    def create_table(self, table_name):
        self.table_service.create_table(table_name)

    def insert_entity_table(self, table_name, entity):
        etag = self.table_service.insert_or_replace_entity(table_name, entity)
        return etag
    
    def update_entity_table(self, table_name, entity):
        etag = self.table_service.update_entity(table_name, entity)
        return etag

    def exist_table(self, table_name):
        return self.table_service.exists(table_name)

    def get_entity_table(self, table_name, partition_key, row_key):
        return self.table_service.get_entity(
            table_name, partition_key, row_key)

    def get_all_entities_table(self, table_name):
        return self.table_service.query_entities(table_name)
        
