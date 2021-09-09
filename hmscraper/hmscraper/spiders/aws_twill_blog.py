import scrapy
import json
import re
from scrapy import signals
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest
import boto3
from json import JSONEncoder
import os
import datetime
import requests
from bs4 import BeautifulSoup


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

    name = 'aws-twill-blog'

    def __init__(self, *args, **kwargs):
        self.url = kwargs.get('url') 
    
        self.start_urls = self.url

        self.base_url = self.url.strip('/')
        self.check_url = self.base_url.replace("http://", '').replace("https://", '').split("/")[0]

        self.base_url_link = re.search('.*(/.*/(.*)/)', self.base_url)
        self.base_url_link = self.base_url_link.group(0).strip("/")

        self.parsed_base_url = re.search('(\\b(?!www\\b)(?!http|https\\b)\w+)(\..*)', self.base_url)
        self.parsed_base_url = self.parsed_base_url.group(1)

        self.start_urls = [f'{self.base_url}']
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
        request = scrapy.Request(response.urljoin(self.url), callback=self.parse_api, headers=self.headers)
        yield request

    # Getting blog pages from API
    def parse_api(self, response):

        # Converting response to JSON
        raw_data = response.body
        data = json.loads(raw_data)

        # data for urls
        jsonData = data["data"]

        # print(jsonData)

        # Ranges of pages if the blogs have more than 1 page
        var_from = data["from"]
        var_last_page = data["last_page"]

        # Parses JSON data to get all blog urls
        for blog in jsonData:
            if blog['seo']['json_schema'] != None:
                url = blog['seo']['json_schema']['url']
                blog_urls.add(str(url))

        # Conditional to see if there's other pages for blogs. If so, then we need to hit this URL and do the same.
        if var_from == var_last_page:
            # Then we have all of the blogs, send these to parse_blog_links
            for url in blog_urls:
                # Adding local URL to URL set, which gets dumped into a text file at the end.
                url_set.add(str(url))
                yield SplashRequest(response.urljoin(url), callback=self.parse_blog_links,  args={'wait': 0.5}, headers=self.headers)
        
        # If the blogs have more then 1 page of content
        else:
            
            # Getting the range of the blog pages. 
            # This use used to get the all of the blog pages so we can hit every URL.
            blog_range = [*range(var_from, var_last_page+1, 1)]
            blog_range.remove(1)

            for blog_page in blog_range:

                # Page of additional blogs
                page_query = self.base_url+"?page="+str(blog_page)

                # API request response
                resp = requests.get(page_query)
                resp_data = resp.text

                # Parsing JSON response and adding pages to blog_urls
                blog_page_data = json.loads(str(resp_data))

                # JSON data we're working with
                jsonData = blog_page_data["data"]

                # Parsing the JSON data to get the URLs
                for blog in jsonData:
                    url = blog['seo']['json_schema']['url']
                    blog_urls.add(str(url))

            # Now we should have all of the URLs in a dataset. 
            # Parse urls in the set
            for url in blog_urls:
                # Adding local URL to URL set, which gets dumped into a text file at the end.
                url_set.add(str(url))
                yield SplashRequest(url, callback=self.parse_blog_links,  args={'wait': 0.5}, headers=self.headers)
 

    # Go through links on blog pages
    def parse_blog_links(self, response):
        blog_response_code = response.status
        blog_url = response.url

        # For each link on the page
        for link in response.css('a::attr(href)').getall():

            if "mailto:" in link or "tel:" in link:
                link_type = "Mailto/Tel"
                yield from self.blog_dump_null(blog_url, blog_response_code, link, link_type)

            else:
                # Something to consider here - if url starts with. 
                # There could be a redirect link here which could flag an external URL as an internal link. 
                if self.check_url in link or link.startswith("/"):
                    link_type = "Local"

                    if link.startswith("/"):
                        link = self.url.replace('/api/posts/', '') + link
                        
                        # Using regex to remove the /api/posts/ from the link. Then we request the URL and get response code in the following request. 
                        # blog_pattern = r'.*(/.*/(.*)/)'
                        # link_parsed = re.sub(blog_pattern, '', link) + link
                else:
                    link_type = "External"

                # To get the response code, we run this through scrapy.Request(). We clean up the URL with removing the port number that's appeneded after the TLD in the request.url
                # Example: https://cubbank.com:443/sample_page > https://cubbank.com/sample_page
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
            "Link": response.url.replace(":443","").replace(":80","").strip("/"),
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
        txt_file_name = str("./links/"+d+"_blog_"+file_name+"-links.txt")
        json_file_name = str("./links/"+d+"_blog_"+file_name+"-links.json")
        csv_file_name = str("./reports/"+d+"_blog_"+file_name+".csv")
        lorem_file_name = str("./lorem/"+d+"_blog_"+file_name+"-lorem-check.txt")

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
        client.upload_file(txt_file_name, 'daily-link-check', m+"/links/"+d+"_blog_"+file_name+"-links.txt")
        client.upload_file(json_file_name, 'daily-link-check', m+"/links/"+d+"_blog_"+file_name+"-links.json")
        client.upload_file(csv_file_name, 'daily-link-check', m+"/reports/"+d+"_blog_"+file_name+"-check.csv")