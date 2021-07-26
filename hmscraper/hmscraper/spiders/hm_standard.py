import scrapy
from scrapy import signals
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest

# URL here
base_url = "https://raque.hatfield.marketing/"
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

    rules = [
        Rule(LinkExtractor(), callback='parse_data', follow=True),
    ]

    def parse(self, response):
        for link in response.css('a::attr(href)').getall():

            page_response_code = response.status
            # If the link has mailto or tel, don't process since this will fail. Call page_dump_null
            if "mailto:" in link or "tel:" in link:
                yield from self.page_dump_null(response.urljoin(link), response.status, link, "Mailto/Tel")

            else:
                # Send all links to parse_data function
                yield SplashRequest(response.urljoin(link), callback=self.parse_data, args={'wait': 0.5}, meta={'original_url': link, 'original_url_response_code': page_response_code})

    def parse_data(self, response):

        page_response_code = response.status
        page_url = response.url
        links = response.css('a::attr(href)').getall()

        link_text = response.xpath('//div[@id="app"]//text()').extract()
        link_string = str(link_text)


        for link in links:

            # If mailto or tel in link
            # else if the link is local
            # else - the URL is an external link
            if "mailto:" in link or "tel:" in link:
                link_type = "Mailto/Tel"
                yield from self.page_dump_null(page_url, page_response_code, link, link_type)

            elif check_url in link or link.startswith("/"):

                link_type = "Local"

                if link.startswith("/"):
                    link = base_url+link

                # Adding local URL to URL set, which gets dumped into a text file at the end.
                # This is used to run local links through the additinoal scripts
                url_set.add(str(link))

            else:
                link_type = "External"

            # Cleaning up page URL since Splash adds the port at the end of the URL
            if page_url.startswith('/'):
                page_url = base_url+response.meta['original_url']
            
            page_url = page_url.replace(":443","").replace(":80","").strip("/")
            
            # Dumping output
            yield {
                "Page": page_url,
                "Page Response": page_response_code,
                "Link": link,
                "Link Type": link_type,
                "Link Response": response.status,
            }
        
        # Lorem Ipsum Checker
        for l in lorem:
            if l in link_string:
                print(f'Found {l} in {page_url}')
                lorem_url_set.add(page_url)
                break

    def page_dump_null(self, page_url, page_response_code, link, link_type):

        # SplashRequest appends the port number at the end on original request. Removing these if detected.
        page_url = page_url.replace(":443","").replace(":80","").strip("/")

        yield {
            "Page": page_url,
            "Page Response": page_response_code,
            "Link": link,
            "Link Type": link_type,
            "Link Response": "N/A",
        }

    # When the spider is completed, all local urls are dumped to a txt file.
    def spider_closed(self, spider):

        # File name
        name = check_url.replace("http://", '').replace("https://", '').split("/")[0].split(".")

        # Writing local URLs to txt file as name of site
        f = open(name[0] + "-links.txt", 'w+')
        f.write('\n'.join(map(str, url_set)))
        f.close()

        # Conditional for URLs that contain lorem ipsum.
        if lorem_url_set:
            lf = open(name[0] + "-lorem-check.txt", 'w+')
            lf.write('\n'.join(map(str, lorem_url_set)))