# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import datetime
from datetime import datetime
import json
import os
from scrapy.exporters import JsonItemExporter
from scrapy import signals
from azure.storage.blob import BlobServiceClient
from scrapy.exceptions import NotConfigured
import logging
import psycopg2
from psycopg2.extras import execute_values


from azure.core.exceptions import ClientAuthenticationError
from itemadapter import ItemAdapter


# Este pipeline define valores padrão para os campos do item, caso eles não estejam presentes.


class DefaultValuesPipeline(object):
    """
    Ensures that every field defined in the Scrapy Item has a default value (None)
    if it was not scraped, and logs a warning for each missing field.
    """
    def process_item(self, item, spider):
        """
        Dynamically checks all fields defined in the item's class.
        """
        # Itera sobre todos os campos definidos na classe do seu Item (ex: ProductItem)
        for field in item.fields:
            # Verifica se o campo não foi preenchido pelo spider
            if field not in item:
                # Loga um aviso usando o logger do spider (melhor prática)
                spider.logger.warning(f"[DefaultValuesPipeline] Field '{field}' is missing. Setting to None.")
                # Define o valor padrão como None
                item.setdefault(field, None)
        return item


class AzureBlobStoragePipeline:
    def __init__(self, account_name, account_key, container_name):
        self.account_name = account_name
        self.account_key = account_key
        self.container_name = container_name
        self.blob_service_client = None
        self.container_client = None
        self.items = [] # Irá armazenar strings JSON, não dicionários

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool("AZURE_ENABLED", False):
            raise NotConfigured("Azure Blob Storage pipeline não está ativado.")
        account_name = crawler.settings.get("AZURE_ACCOUNT_NAME")
        account_key = crawler.settings.get("AZURE_ACCOUNT_KEY")
        container_name = crawler.settings.get("AZURE_CONTAINER_NAME")
        if not all([account_name, account_key, container_name]):
            raise NotConfigured("Configurações do Azure Blob Storage estão faltando.")
        return cls(account_name, account_key, container_name)

    def open_spider(self, spider):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            connection_string = f"DefaultEndpointsProtocol=https;AccountName={self.account_name};AccountKey={self.account_key};EndpointSuffix=core.windows.net"
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
            self.logger.info("Conectado com sucesso ao Azure Blob Storage.")
        except Exception as e:
            self.logger.error(f"Falha ao conectar ao Azure Blob Storage: {e}")
            raise NotConfigured("Não foi possível conectar ao Azure Blob Storage.")

    def process_item(self, item, spider):
        """Converte cada item para uma string JSON e a anexa à lista."""
        line = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False)
        self.items.append(line)
        return item

    def close_spider(self, spider):
        """
        Junta as strings JSON com novas linhas para criar o conteúdo .jsonl
        e faz o upload para o Azure usando o nome de arquivo correto.
        """
        if not self.items:
            self.logger.warning("Nenhum item foi raspado, pulando o upload para o Azure.")
            return

        # --- A CORREÇÃO ESTÁ AQUI ---
        # Pega o caminho do arquivo diretamente das configurações do spider, que já termina em .jsonl.
        # Nenhuma substituição de string é necessária.
        blob_path = spider.custom_settings.get("FEED_URI")
        log_file_path = spider.custom_settings.get("LOG_FILE")

        if not blob_path:
            self.logger.error("FEED_URI não encontrado nas configurações do spider. Não é possível fazer o upload.")
            return

        try:
            # Junta todas as strings JSON individuais com um caractere de nova linha
            jsonl_data = "\n".join(self.items)
            blob_client = self.container_client.get_blob_client(blob_path)
            
            self.logger.info(f"Fazendo upload de {len(self.items)} itens para o Azure Blob Storage em: {self.container_name}/{blob_path}")
            blob_client.upload_blob(jsonl_data.encode("utf-8"), overwrite=True)
            self.logger.info("Upload de dados bem-sucedido.")

        except ClientAuthenticationError:
            self.logger.critical("FALHA DE AUTENTICAÇÃO NO AZURE. Verifique se a sua 'AZURE_ACCOUNT_KEY' está correta.")
        except Exception as e:
            self.logger.error(f"Ocorreu um erro inesperado durante o upload dos dados: {e}")

        # Lógica de upload do log (permanece a mesma)
        if log_file_path:
            try:
                with open(log_file_path, "rb") as log_file:
                    blob_client = self.container_client.get_blob_client(log_file_path)
                    blob_client.upload_blob(log_file, overwrite=True)
                    self.logger.info(f"Arquivo de log enviado com sucesso para o Azure: {log_file_path}")
            except FileNotFoundError:
                self.logger.warning(f"Arquivo de log não encontrado em {log_file_path}, pulando o upload do log.")



class SitemapPostgresPipeline:
    def __init__(self, host, database, user, password, port, table):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.table = table
    
    def parse_flexible_date(self, date_str, spider):
        formats = [
            "%d/%m/%Y %H:%M:%S",          # ex: 06/04/2025 13:45:00
            "%d/%m/%Y",                   # ex: 06/04/2025
            "%Y-%m-%dT%H:%M:%S.%fZ",      # ex: 2025-04-03T15:36:45.175Z
            "%Y-%m-%dT%H:%M:%S.%f",       # ex: 2025-04-06T12:09:27.265018
            "%Y-%m-%dT%H:%M:%S",          # ex: 2025-04-06T12:09:27
            "%Y-%m-%d",                   # ex: 2025-04-06
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        spider.logger.error(f"[Pipeline] Formato de data não reconhecido: {date_str}")
        raise ValueError(f"Formato de data não suportado: {date_str}")

    @classmethod
    def from_crawler(cls, crawler):
        host = crawler.settings.get("DB_HOST")
        database = crawler.settings.get("DB_NAME")
        user = crawler.settings.get("DB_USERNAME")
        password = crawler.settings.get("DB_PASSWORD")
        port = crawler.settings.get("DB_PORT", "5432")
        table = crawler.settings.get("DB_TABLE_NAME")

        return cls(host, database, user, password, port, table)

    def open_spider(self, spider):
        self.connection = psycopg2.connect(
            f"dbname={self.database} user={self.user} host={self.host} password={self.password} port={self.port}"
        )

        spider.logger.info("Connection established!")
        # Create cursor, used to execute commands
        self.cursor = self.connection.cursor()

        # Create table if it does not exist
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                id SERIAL PRIMARY KEY,
                market_name VARCHAR(255),
                initial_page VARCHAR(255),
                robots_page VARCHAR(255),
                sitemap_page VARCHAR(255),
                loc TEXT,
                last_mod TIMESTAMP,
                date_extracted TIMESTAMP
            )
        """
        )

    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.commit()
            self.connection.close()

    def process_item(self, item, spider):
        item_last_mod = self.parse_flexible_date(item["last_mod"], spider)
        item_date_extracted = self.parse_flexible_date(item["date_extracted"], spider)

        # Define the insertion statement
        sql = f"""
            INSERT INTO {self.table}
            (market_name, initial_page, robots_page, sitemap_page, loc, last_mod, date_extracted)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        data = (
            item["market_name"],
            item["initial_page"],
            item["robots_page"],
            item["sitemap_page"],
            item["loc"],
            item_last_mod,
            item_date_extracted,
        )

        self.cursor.execute(sql, data)
        self.connection.commit()

        spider.logger.info("Item added into database")

        return item

class RemoveDuplicatesPipeline:
    def __init__(self, host, database, user, password, port, table):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.table = table

    @classmethod
    def from_crawler(cls, crawler):
        host = crawler.settings.get("DB_HOST")
        database = crawler.settings.get("DB_NAME")
        user = crawler.settings.get("DB_USERNAME")
        password = crawler.settings.get("DB_PASSWORD")
        port = crawler.settings.get("DB_PORT", "5432")
        table = crawler.settings.get("DB_TABLE_NAME")

        return cls(host, database, user, password, port, table)

    def open_spider(self, spider):
        self.connection = psycopg2.connect(
            f"dbname={self.database} user={self.user} host={self.host} password={self.password} port={self.port}"
        )
        self.cursor = self.connection.cursor()

    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.commit()
            self.connection.close()

    def process_item(self, item, spider):
        # Remove duplicatas com base nas colunas desejadas
        self.cursor.execute(
            f"""
            DELETE FROM {self.table} a
            USING {self.table} b
            WHERE a.id > b.id AND 
                  a.market_name = b.market_name AND
                  a.initial_page = b.initial_page AND
                  a.robots_page = b.robots_page AND
                  a.sitemap_page = b.sitemap_page AND
                  a.loc = b.loc
            """
        )
        spider.logger.info("Duplicatas removidas da tabela.")

        return item
