import scrapy
from scrapy import signals
from scrapy.http import headers
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest

# URL here
base_url = "https://doctor-medicare.hatfield.marketing/"

# Parsing url
base_url = base_url.strip("/")
check_url = base_url.replace("http://", '').replace("https://", '').split("/")[0]

# Storing urls for pages we've found to dump into a text file
url_set = set()
links = []
pages = []

class HMScraper(scrapy.Spider):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
        "sec-ch-ua-mobile": "?0",
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HMScraper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    name = "standard"
    start_urls = []
    start_urls.append(base_url)
    allowed_domains = [check_url]
    deny = ["r/^mailto:/", "/^tel:/"]

    def parse(self, response):
        for link in response.XPath("//script[contains(@src, 'googletagmanager')]").getall():

            # If the link has mailto or tel, don't process since this will fail. Call page_dump_null
            if "mailto:" in link or "tel:" in link:
                yield from self.page_dump_null(response.request.url, link, "Mailto/Tel", "N/A")
            else:
                # Send all links to parse_data function
                yield SplashRequest(response.urljoin(link), callback=self.parse_data, headers=self.headers, meta={'original_url': link})


    def spider_closed(self, spider):
    # When the spider is completed, all local urls are dumped to a txt file.

        # File name
        name = check_url.replace("http://", '').replace("https://", '').split("/")[0].split(".")

        # Writing local URLs to txt file as name of site
        f = open(name[0] + "-links.txt", 'w+')
        f.write('\n'.join(map(str, url_set)))
        f.close()
