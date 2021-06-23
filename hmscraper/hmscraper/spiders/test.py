import scrapy
from scrapy import signals
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest
import logging
import base64
import json

# URL here
base_url = "https://raque.hatfield.marketing"
base_url = base_url.strip("/")


check_url = base_url.replace("http://", '').replace("https://", '').split("/")[0]

# Storing urls for pages we've found to dump into a text file
url_set = set()

links = []
pages = []

lorem_string = "Lorem ipsum dolor amet consectetur adipiscing elit eiusmod tempor incididunt labore dolore magna aliqua enim minim veniam quis nostrud exercitation ullamco laboris nisi aliquip commodo consequat Duis aute irure dolor reprehenderit voluptate velit esse cillum dolore fugiat nulla pariatur Excepteur sint occaecat cupidatat proident culpa officia deserunt mollit laborum".split()

lorem = set()

for w in lorem_string:
    lorem.add(" " + w + " ")

# Adding 'lorem ' incase text starts with lorem
lorem.add("lorem ")
lorem_url_set = set()

class HMScraper(scrapy.Spider):

    # Have a lua script here to make our requests. This is needed since we're using SplashRequest to make the request for us, and the splash request.status doesn't return the correct status code we're looking for. 
    # Referring to https://github.com/scrapy-plugins/scrapy-splash
    # Need to get the Lua script to return the URL for 
    # ...
    lua_script = """
        function main(splash)
                assert(splash:go(splash.args.url))
            })

            return {
                url = splash:url(),
                headers = d.headers,
                http_status = last_response.status,
                cookies = splash:get_cookies(),
                html = splash:html(),
            }
        end
        """

    name = "testing"
    start_urls = []
    start_urls.append(base_url)
    allowed_domains = [check_url]
    deny = ["r/^mailto:/", "/^tel:/"]

    rules = [
        Rule(LinkExtractor(), callback='parse_data', follow=True),
    ]

    def parse(self, response):

        # if response.status == 404:
        #     yield from self.page_dump_null(response.urljoin(link), response.status, link, "Mailto/Tel", "N/A")

        for link in response.css('a::attr(href)').getall():
        
            page_response_code = response.status
            # If the link has mailto or tel, don't process since this will fail. Call page_dump_null
            if "mailto:" in link or "tel:" in link:
                # yield from self.page_dump_null(response.urljoin(link), response.status, link, "Mailto/Tel", "N/A")
                break

            else:
                # Send all links to parse_data function
                yield SplashRequest(response.urljoin(link), callback=self.parse_data, endpoint='execute', magic_response=True, meta={'handle_httpstatus_all': True, 'original_url': link, 'original_url_response_code': page_response_code}, args={'lua_source': self.lua_script})

    def parse_data(self, response):
        self.logger.info(response.reqeust.url)
        self.logger.info(response.status)
