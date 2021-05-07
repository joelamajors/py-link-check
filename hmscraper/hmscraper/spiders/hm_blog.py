import scrapy
import json
from scrapy import signals
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest

# URL here
base_url = "https://aac.hatfield.marketing"

base_url = base_url.strip("/")

# Storing urls in the set, then exporting at the end
blog_urls = set()

check_url = base_url.replace("http://", '').replace("https://", '').split("/")[0]

# Storing urls for pages we've found to dump into a text file
url_set = set()

class HmblogSpider(scrapy.Spider):

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HmblogSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    rules = [
        Rule(LinkExtractor(allow=(), deny=("r/^mailto:/", "r/^tel:/"))),
    ]

    name = 'hmblog_twill'
    start_urls = [f'{base_url}/blog?all-page=1']
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization":"null null",
        "Referer": f'{base_url}/blog',
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
        "sec-ch-ua-mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    # Gets API URL, then goes to parse API. 
    def parse(self, response):
        url = f'{base_url}/api/posts?blog%5B%5D=1&count=6&locale=en&order-by=publish_start_date'
        request = scrapy.Request(url, callback=self.parse_api, headers=self.headers)
        yield request

    # Getting blog pages from API
    def parse_api(self, response):

        # Converting response to JSON
        raw_data = response.body
        data = json.loads(raw_data)

        # Getting blog URLs
        blog_data = data['data']

        # Extract blog_urls from each blog that's loaded
        for blog in blog_data:
            blog_url = base_url + blog["full_slug"]
            blog_urls.add(str(blog_url))

        # If the blog page has more content to load
        if data["next_page_url"]:
            url = data["next_page_url"]
            request = scrapy.Request(url, callback=self.parse_api, headers=self.headers)
            yield request
        else: 
            for url in blog_urls:
                # Adding local URL to URL set, which gets dumped into a text file at the end.
                url_set.add(str(link))
                yield SplashRequest(url, callback=self.parse_blog_links,  args={'wait': 0.5}, headers=self.headers)
 

    # Go through links on blog pages, then parses dump of logs
    def parse_blog_links(self, response):
        blog_response_code = response.status
        blog_url = response.url

        for link in response.css('a::attr(href)').getall():

            if "mailto:" in link or "tel:" in link:
                link_type = "Mailto/Tel"
                yield from self.blog_dump_null(blog_url, blog_response_code, link, link_type)

            else:
                if check_url in link or link.startswith("/"):
                    link_type = "Local"

                    if link.startswith("/"):
                        link = base_url+link

                else:
                    link_type = "External"

                yield scrapy.Request(link, callback=self.blog_dump, meta={ 'blog_response_code': blog_response_code, 'blog_url': blog_url, 'link_type': link_type }, headers=self.headers)


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
        name = check_url.replace("http://", '').replace("https://", '').split("/")[0].split(".")
        
        # Writing URLs to txt file as name of site
        f = open(name[0]+"-blog-links.txt", 'w+')
        f.write('\n'.join(map(str, url_set)))