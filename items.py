import scrapy
from itemloaders.processors import TakeFirst, MapCompose

def clean_text(value):
    """Uma função de limpeza simples para remover espaços em branco."""
    return value.strip() if value else None

class SitemapItem(scrapy.Item):
    """
    Define os campos para um item de sitemap.
    Usa TakeFirst() para garantir que cada campo armazene um valor único, não uma lista.
    """
    market_name = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    initial_page = scrapy.Field(
        output_processor=TakeFirst()
    )
    robots_page = scrapy.Field(
        output_processor=TakeFirst()
    )
    sitemap_page = scrapy.Field(
        output_processor=TakeFirst()
    )
    loc = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    last_mod = scrapy.Field(
        output_processor=TakeFirst()
    )
    date_extracted = scrapy.Field(
        output_processor=TakeFirst()
    )