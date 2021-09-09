import scrapy
import json
import re
from scrapy import signals
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest

# Storing urls for pages we've found to dump into a text file
url_set = set()

blog_urls = set()

links = []
pages = []

lorem_string = "Lorem ipsum dolor amet consectetur adipiscing elit eiusmod tempor incididunt labore dolore magna aliqua enim minim veniam quis nostrud exercitation ullamco laboris nisi aliquip commodo consequat Duis aute irure dolor reprehenderit voluptate velit esse cillum dolore fugiat nulla pariatur Excepteur sint occaecat cupidatat proident culpa officia deserunt mollit laborum".split()

lorem = set()

for w in lorem_string:
    lorem.add(" " + w + " ")

# Adding 'lorem ' incase text starts with lorem
lorem.add("lorem ")
lorem_url_set = set()

class HmblogSpider(scrapy.Spider):

    name = 'blog-twill'

    def __init__(self, *args, **kwargs):
        self.url = kwargs.get('url') 
    
        self.start_urls = self.url

        self.base_url = self.url.strip('/')
        self.check_url = self.base_url.replace("http://", '').replace("https://", '').split("/")[0]

        self.parsed_base_url = re.search('.*(/.*/(.*)/)', self.base_url)
        self.parsed_base_url = self.parsed_base_url.group(0).strip("/")

        self.start_urls = [f'{self.base_url}?all-page=1']
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Authorization":"null null",
            "Referer": f'{self.base_url}',
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        super(HmblogSpider, self).__init__(*args, **kwargs)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HmblogSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    rules = [
        Rule(LinkExtractor(allow=(), deny=("r/^mailto:/", "r/^tel:/"))),
    ]

    # Gets API URL, then goes to parse API. 
    def parse(self, response):
        url = f'{self.parsed_base_url}/api/posts?blog%5B%5D=1&count=6&locale=en&order-by=publish_start_date&locale=en'

        request = scrapy.Request(response.urljoin(url), callback=self.parse_blog_links, headers=self.headers)
        yield request

    # # Getting blog pages from API
    # def parse_api(self, response):

    #     # Converting response to JSON
    #     raw_data = response.body
    #     data = json.loads(raw_data)

    #     # Getting blog URLs
    #     blog_data = data['data']

    #     # Extract blog_urls from each blog that's loaded
    #     for blog in blog_data:
    #         blog_url = self.parsed_base_url + blog["full_slug"]
    #         blog_urls.add(str(blog_url))

    #     # If the blog page has more content to load
    #     if data["next_page_url"]:
    #         url = data["next_page_url"]
    #         request = scrapy.Request(response.urljoin(url), callback=self.parse_api, headers=self.headers)
    #         yield request
    #     else: 
    #         for url in blog_urls:
    #             # Adding local URL to URL set, which gets dumped into a text file at the end.
    #             url_set.add(str(url))
    #             yield SplashRequest(response.urljoin(url), callback=self.parse_blog_links,  args={'wait': 0.5}, headers=self.headers)
 

    # Go through links on blog pages, then parses dump of logs
    def parse_blog_links(self, response):
        blog_response_code = response.status
        blog_url = response.url

        for link in response.css('a::attr(href)').getall():

            if "mailto:" in link or "tel:" in link:
                link_type = "Mailto/Tel"
                yield from self.blog_dump_null(blog_url, blog_response_code, link, link_type)

            else:
                if self.check_url in link or link.startswith("/"):
                    link_type = "Local"

                    if link.startswith("/"):
                        link = self.parsed_base_url+link

                else:
                    link_type = "External"
                
                yield scrapy.Request(response.urljoin(link), callback=self.blog_dump, meta={ 'blog_response_code': blog_response_code, 'blog_url': blog_url, 'link_type': link_type }, headers=self.headers)


    # Dumping all of the data
    def blog_dump(self, response):

        # Retreiving meta to pass to blog_dump
        blog_url = response.meta["blog_url"]
        blog_response_code = response.meta["blog_response_code"]
        link_type = response.meta["link_type"]

        yield {
            "Page": blog_url,
            "Page Response": blog_response_code,
            "Link": response.url,
            "Link Type": link_type,
            "Link Response": response.status,
        }

    # Dumping data for mailto/tel links since these are not checked. 
    def blog_dump_null(self, blog_url, blog_response_code, link, link_type):

        yield {
            "Page": blog_url,
            "Page Response": blog_response_code,
            "Link": link,
            "Link Type": link_type,
            "Link Response": "N/A",
        }

    # When the spider is completed, all local urls are dumped to a txt file.
    def spider_closed(self, spider):
        # File name
        name = self.check_url.replace("http://", '').replace("https://", '').split("/")[0].split(".")
        
        # Writing URLs to txt file as name of site
        f = open(name[0]+"-blog-links.txt", 'w+')
        f.write('\n'.join(map(str, url_set)))