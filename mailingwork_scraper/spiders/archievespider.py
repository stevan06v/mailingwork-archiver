import scrapy

from mailingwork_scraper.items import MailingworkScraperItem


class ArchiveSpider(scrapy.Spider):
    name = "archievespider"
    start_urls = ["https://login.mailingwork.de/-ea-list/3886/P9hLk/1/fQ5xxQrwF2"]

    def parse(self, response, **kwargs):
        for row in response.xpath("//tr"):
            item = MailingworkScraperItem()

            item["date"] = row.xpath("td[1]/text()").get(default="").strip()
            item["name"] = row.xpath("td[2]/strong/text()").get(default="").strip()

            item["html_link"] = None
            item["pdf_link"] = None
            for link in row.xpath("td[3]/a"):
                href = link.xpath("@href").get()
                if href:
                    href = response.urljoin(href)

                    if "html" in href:
                        item["html_link"] = href
                        item["pdf_link"] = href.replace("/html", "/pdf")
                        yield scrapy.Request(url=href, callback=self.parse_images, meta={"item": item})

            yield item

    def parse_images(self, response):
        item = response.meta["item"]
        item["images"] = response.xpath("//img/@src").getall()
        yield item
