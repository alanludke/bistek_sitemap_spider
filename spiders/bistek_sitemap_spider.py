import json
import scrapy
from datetime import datetime
import time
import logging
import re
import sys
from scrapy.loader import ItemLoader
import xmltodict
import os

from items import SitemapItem

# Ensure item and utility imports are correct for your project structure
from utils.utils import create_dir_if_doesnt_exists


FORMATTED_DATE = time.strftime("%Y%m%d")
FORMATTED_TIMESTAMP = time.strftime("%H%M%S")

class BistekSitemapSpider(scrapy.Spider):
    """
    Scrapes the main sitemap to discover all catalog sitemap URLs.
    This spider is the first stage in the data collection pipeline and
    saves its output in a partitioned directory structure.
    """
    name = "bistek_sitemap_spider"

    # --- Start of Partitioning Logic ---
    now = datetime.now()
        
    # 1. Define a estrutura de pastas compartilhada e o nome base do arquivo
    # Exemplo de partition_path: "year=2025/month=07/day=20"
    partition_path = f"year={now.year}/month={now.month:02d}/day={now.day:02d}"
    run_timestamp = now.strftime('%Y%m%d_%H%M%S')
    file_name_base = f"{name}_{run_timestamp}"

    # 2. Constrói os caminhos completos, agora sem o nome do spider no diretório
    feed_uri = f"data/{partition_path}/{file_name_base}.jsonl"
    log_file = f"logs/{partition_path}/{file_name_base}.log"
    # --- Fim da Lógica de Particionamento ---

    # Atualiza as configurações do spider com os novos caminhos
    custom_settings = {
        "LOG_FILE": log_file,
        "FEED_URI": feed_uri,
        "FEED_FORMAT": "jsonlines", # Melhor formato para data lakes
        "FEED_EXPORT_ENCODING": "utf-8",
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Cria os diretórios de saída necessários
    # A função de utilidade deve ser capaz de criar diretórios aninhados
    create_dir_if_doesnt_exists(name, f"data/{partition_path}/")
    create_dir_if_doesnt_exists(name, f"logs/{partition_path}/")

    logging.info(f"Spider '{name}' inicializado.")
    logging.info(f"Saída de dados será salva em: {feed_uri}")
    logging.info(f"Saída de logs será salva em: {log_file}")

    def start_requests(self):
        """
        This method is overridden to add a User-Agent header to the initial request,
        preventing the 429 "Too Many Requests" error.
        """
        url = "https://www.bistek.com.br/sitemap.xml"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.logger.info(f"Sending initial request with custom User-Agent to {url}")
        yield scrapy.Request(url, headers=headers, callback=self.parse)


    def parse(self, response):
        """
        Parses the main sitemap.xml file to extract URLs for individual catalog sitemaps.
        """
        self.logger.info(f"Successfully downloaded main sitemap. Parsing entries...")

        response.selector.register_namespace("s", "http://www.sitemaps.org/schemas/sitemap/0.9")
        sitemap_nodes = response.xpath("//s:sitemap")

        self.logger.info(f"Found {len(sitemap_nodes)} sitemap entries to process.")
        if not sitemap_nodes:
            self.logger.warning("No sitemap entries found. Check if the XML structure has changed.")
            return

        for node in sitemap_nodes:
            loader = ItemLoader(item=SitemapItem(), selector=node)
            
            # Populate with static metadata
            loader.add_value('market_name', self.name.split('_')[0]) # Use base name 'bistek'
            loader.add_value('initial_page', "https://www.bistek.com.br/")
            loader.add_value('robots_page', "https://www.bistek.com.br/robots.txt")
            loader.add_value('sitemap_page', response.url)
            loader.add_value('date_extracted', datetime.now().isoformat())

            # Extract data from the XML node using XPath
            loader.add_xpath('loc', './s:loc/text()') 
            loader.add_xpath('last_mod', './s:lastmod/text()')
            
            yield loader.load_item()

