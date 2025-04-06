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

sys.path.append("..")
from items import SitemapItem

from utils import *


FORMATTED_DATE = time.strftime("%Y%m%d")
FORMATTED_TIMESTAMP = time.strftime("%H%M%S")

# Defines the Spider responsible to scrape data from bistek' supermarket in a simplified way
class BistekSitemapSpider(scrapy.Spider):
    name = "bistek_sitemap_spider"

    start_urls = ["https://www.bistek.com.br/sitemap.xml"]

    create_dir_if_doesnt_exists(name, f"logs/{FORMATTED_DATE}/")
    create_dir_if_doesnt_exists(name, f"data/{FORMATTED_DATE}/")

    filepath = f"{FORMATTED_DATE}/{name}_{FORMATTED_DATE}_{FORMATTED_TIMESTAMP}"

    custom_settings = {
        "LOG_FILE": f"logs/{filepath}.log",
        "FEED_URI": f"data/{filepath}.json",
    }

    def parse(self, response):
        item = SitemapItem()

        data_dict = xmltodict.parse(response.text)
        # data_dict_str = json.dumps(data_dict)

        market_name = "bistek"
        initial_page = "https://www.bistek.com.br/"
        robots_page = "https://www.bistek.com.br/robots.txt"
        sitemap_page = response.url

        for each_item in data_dict["sitemapindex"]["sitemap"]:

            item["market_name"] = self.name
            item["initial_page"] = initial_page
            item["robots_page"] = robots_page
            item["sitemap_page"] = sitemap_page
            item["loc"] = each_item["loc"]
            item["last_mod"] = each_item["lastmod"]
            item["date_extracted"] = datetime.now().isoformat()

            yield item
