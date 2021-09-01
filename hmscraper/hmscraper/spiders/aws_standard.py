import scrapy
from scrapy import signals
from scrapy import spiders
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest
import json
from json import JSONEncoder
import os
import datetime
import boto3
import re


'''
This is used to run screenshots tests from AWS via the lambdatest instance. 
This generates the following
- CSV with all respose codes
- txt file with all of the internal pages
- If found, a txt file will be created with links that contain lorem ipsum. 
'''

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


class scraperAWS(scrapy.Spider):

    name = "aws-standard"    

    def __init__(self, *args, **kwargs):
        self.url = kwargs.get('url') 
        
        self.start_urls = self.url

        self.base_url = self.url.strip('/')
        self.check_url = self.base_url.replace("http://", '').replace("https://", '').split("/")[0]

        super(scraperAWS, self).__init__(*args, **kwargs)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(scraperAWS, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    deny = ["r/^mailto:/", "/^tel:/"]

    rules = [
        Rule(LinkExtractor(), callback='parse_data', follow=True),
    ]

    def start_requests(self):
    
        # Call back, goes to parse function
        yield scrapy.Request(self.start_urls, callback=self.parse)

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

            elif self.check_url in link or link.startswith("/"):

                link_type = "Local"

                if link.startswith("/"):
                    link = self.base_url+link

                # Adding local URL to URL set, which gets dumped into a text file at the end.
                # This is used to run local links through the additinoal scripts
                url_set.add(str(link.strip()))

            else:
                link_type = "External"

            # Cleaning up page URL since Splash adds the port at the end of the URL
            if page_url.startswith('/'):

                page_url = self.base_url+response.meta['original_url'].strip('/')
            
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

        client = boto3.client('s3')

        # Generate date for report files
        x = datetime.datetime.now()
        d = x.strftime('%m-%d-%y')
        m = x.strftime('%b')

        # Files should be created. But if not, then create them
        if not os.path.exists('./links'):
            os.makedirs('./links')

        if not os.path.exists('./reports'):
            os.makedirs('./reports')

        if not os.path.exists('./lorem'):
            os.makedirs('./lorem')
        
        # File name, using regex to get file name from url
        base_url_reg = re.search('((\\b(?!www\\b)(?!http|https\\b)\w+))(\..*)', self.base_url)
        file_name = base_url_reg.group(2)

        # File paths for local EC2 instance
        txt_file_name = str("./links/"+d+"_"+file_name+"-links.txt")
        json_file_name = str("./links/"+d+"_"+file_name+"-links.json")
        csv_file_name = str("./reports/"+d+"_"+file_name+".csv")
        lorem_file_name = str("./lorem/"+d+"_"+file_name+"-lorem-check.txt")

        # Used to encode set to JSON
        class setEncoder(JSONEncoder):
            def default(self, obj):
                return list(obj)

        # Writing urls to JSON
        with open(json_file_name,'w+') as file:
            file.write(json.dumps({'urls': url_set}, cls=setEncoder))

        # Writing local URLs to txt file as name of site
        f = open(txt_file_name, 'w+', encoding="utf-8")
        f.write('\n'.join(map(str, url_set)))
        f.close()

        # Conditional for URLs that contain lorem ipsum.
        if lorem_url_set:
            lf = open(lorem_file_name, 'w+')
            lf.write('\n'.join(map(str, lorem_url_set)))

            # If lorem ipsum, upload to S3 bucket
            client.upload_file(lorem_file_name, 'daily-link-check', m+"/lorem/"+d+"_"+file_name+"-lorem-check.txt")

        # Copy files to S3
        client.upload_file(txt_file_name, 'daily-link-check', m+"/links/"+d+"_"+file_name+"-links.txt")
        client.upload_file(json_file_name, 'daily-link-check', m+"/links/"+d+"_"+file_name+"-links.json")
        client.upload_file(csv_file_name, 'daily-link-check', m+"/reports/"+d+"_"+file_name+"-lorem-check.csv")

