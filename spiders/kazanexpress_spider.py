import scrapy
import re

from urllib.parse import urlparse, parse_qs, urlencode, urljoin


class KazanExpressSpider(scrapy.Spider):
    name = 'kazanexpress'

    IDS = [10671]

    ITEMS_PER_PAGE = 100  # Max number is 100

    start_urls = [
        f'https://api.kazanexpress.ru/api/v2/main/search/product?size={100}&page=0&&categoryId={id}' for id in IDS
    ]

    custom_settings = {
        # 'DOWNLOAD_DELAY': 0.25,
        'LOG_LEVEL': 'INFO',
    }

    HEADERS = {
        'Authorization': 'Bearer 25efea2b-ec68-46a0-bf6f-6cd69fe43a91'
    }

    PRODUCT_URL = 'https://api.kazanexpress.ru/api/v2/product/'

    def parse(self, response, page=0):

        for item in response.json()['payload']['products']:
            yield scrapy.Request(
                url=urljoin(self.PRODUCT_URL, str(item['productId'])),
                callback=self.parse_item,
                headers=self.HEADERS,
            )

        if response.json()['payload']['totalProducts'] > self.ITEMS_PER_PAGE * (page + 1):
            parsed = urlparse(response.url)
            query = parse_qs(parsed.query)
            query['page'] = [page + 1]
            url = parsed._replace(query=urlencode(query, doseq=True)).geturl()

            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs=dict(page=page+1))

    def parse_item(self, response):
        yield {
            'name': response.json()['payload']['data']['title'],
            'description': response.json()['payload']['data']['description'],
            'author': self.find_author(response.json()['payload']['data']['attributes'])
        }

    def find_author(self, attributes):
        for attribute in attributes:
            regex = re.search(r'Автор: (.*)', attribute)
            if regex:
                return regex[1]
            return None
