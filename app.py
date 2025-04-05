import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.bistek_sitemap_spider import BistekSitemapSpider


settings = get_project_settings()

settings.set("AZURE_ENABLED", os.environ["AZURE_ENABLED"])
settings.set("AZURE_ACCOUNT_NAME", os.environ["AZURE_ACCOUNT_NAME"])
settings.set("AZURE_ACCOUNT_URL", os.environ["AZURE_ACCOUNT_URL"])
settings.set("AZURE_ACCOUNT_KEY", os.environ["AZURE_ACCOUNT_KEY"])
settings.set("AZURE_CONTAINER_NAME", BistekSitemapSpider.name.replace("_", "-"))


settings.set("DATABASE_ENABLED", os.environ["DATABASE_ENABLED"])
settings.set("DB_HOST", os.environ["DB_HOST"])
settings.set("DB_PORT", os.environ["DB_PORT"])
settings.set("DB_USERNAME", os.environ["DB_USERNAME"])
settings.set("DB_PASSWORD", os.environ["DB_PASSWORD"])
settings.set("DB_NAME", os.environ["DB_NAME"])
settings.set("DB_TABLE_NAME", BistekSitemapSpider.name)


def scrape():

    process = CrawlerProcess(settings)
    process.crawl(BistekSitemapSpider)
    process.start()

scrape()

