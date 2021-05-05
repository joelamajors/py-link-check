import scrapy
import json
from scrapy import signals

# URL here
base_url = "https://aac.hatfield.marketing"

base_url = base_url.strip("/")

# Storing urls in the set, then exporting at the end
blog_urls = set()

class HmblogSpider(scrapy.Spider):

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
            # print(data["next_page_url"])
            url = data["next_page_url"]
            request = scrapy.Request(url, callback=self.parse_api, headers=self.headers)
            yield request
        else: 
            for item in blog_urls:
                yield {
                    "URL": item
                }