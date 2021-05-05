import scrapy
from scrapy import signals
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest

# URL here
check_url = "https://mister-medicare.hatfield.marketing/"
check_url = check_url.strip("/")

# Storing urls for pages we've found to dump into a text file
url_set = set()

class HMScraper(scrapy.Spider):

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HMScraper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    name = "standard"
    start_urls = []
    start_urls.append(check_url)
    check_url = check_url.replace("http://", '').replace("https://", '').split("/")[0]
    allowed_domains = [check_url]
    deny = ["r/^mailto:/", "/^tel:/"]

    rules = [
        Rule(LinkExtractor(allow=(), deny=("r/^mailto:/", "r/^tel:/"))),
    ]

    def parse(self, response):
        for link in response.css('a::attr(href)').getall():
            if "mailto:" in link or "tel:" in link:

                yield {
                    "Page": response.request.url,
                    "Link": link,
                    "Local/External": "N/A",
                    "Mailto/Phone": True,
                    "Response": response.status,
                }

            else:
                url_set.add(str(response.request.url))
                # Using meta to access request URL. 
                yield SplashRequest(response.urljoin(link), callback=self.parse_data, meta={'original_url': link})

    def parse_data(self, response):
        
        links = response.css('a::attr(href)').getall()

        for link in links:

            # If local link or starts with /
            if check_url in link or link.startswith("/"):
                page_type = "Local"

                if link.startswith("/"):
                    link = check_url+link

            else:
                page_type = "External"

                # Getting mailto / tel links
                if "mailto:" in link or "tel:" in link:
                    mail_tel = True
                    page_type = "N/A"
                else:
                    mail_tel = False

                # Logging response code
                print(response)
                status_code = response.status

                # Get Page Info with meta. Adjusting relative URL path
                if response.meta['original_url'].startswith('/'):
                    page = check_url+response.meta['original_url']
                else:
                    page = response.meta['original_url']

                url_set.add(str(page))

                yield {
                    "Page": page,
                    "Link": response.urljoin(link),
                    "Local/External": page_type,
                    "Mailto/Phone": mail_tel,
                    "Response": status_code,
                }

    # When the spider is completed, all local urls are dumped to a txt file.
    def spider_closed(self, spider):
        # File name
        name = check_url.replace("http://", '').replace("https://", '').split("/")[0].split(".")
        
        # Writing URLs to txt file as name of site
        f = open(name[0]+"-links.txt", 'w+')
        f.write('\n'.join(map(str, url_set)))