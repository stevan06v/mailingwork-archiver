# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MailingworkScraperItem(scrapy.Item):
    name = scrapy.Field()
    date = scrapy.Field()
    html_link = scrapy.Field()
    pdf_link = scrapy.Field()
    images = scrapy.Field()
