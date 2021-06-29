import scrapy
from scrapy import signals
from scrapy_splash import SplashRequest

# URL here
base_url = "https://louisville-paving.hatfield.marketing/"

# Parsing url
base_url = base_url.strip("/")
check_url = base_url.replace("http://", '')\
                    .replace("https://", '')\
                    .split("/")[0]

# Storing urls for pages we've found to dump into a text file
url_set = set()
links = []
pages = []
lorem_string = '''Lorem ipsum dolor amet consectetur adipiscing elit eiusmod
                tempor incididunt labore dolore magna aliqua enim minim
                veniam quis nostrud exercitation ullamco laboris nisi
                aliquip commodo consequat Duis aute irure dolor reprehenderit
                voluptate velit esse cillum dolore fugiat nulla pariatur
                Excepteur sint occaecat cupidatat proident culpa officia
                deserunt mollit laborum'''.split()
lorem_set = set()

for word in lorem_string:
    lorem_set.add(" " + word + " ")

# Adding 'lorem ' with no starting space in case text starts with lorem
lorem_set.add("lorem ")

# Storing urls with lorem ipsum
lorem_url_set = set()


class HMScraper(scrapy.Spider):

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
        "sec-ch-ua-mobile": "?0",
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(HMScraper, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        return spider

    name = "standard"
    start_urls = []
    start_urls.append(base_url)
    allowed_domains = [check_url]
    deny = ["r/^mailto:/", "/^tel:/"]
    # rules = [
    #     Rule(LinkExtractor(), callback='parse_data', follow=True),
    # ]

    def parse(self, response):

        for link in response.css('a::attr(href)').getall():
            # If link has mailto or tel, don't process since this will fail.
            # Call page_dump_null
            if "mailto:" in link or "tel:" in link:
                yield from self.page_dump_null(response.request.url,
                                               link,
                                               "Mailto/Tel",
                                               "N/A")
            else:
                # Send all links to parse_data function
                yield SplashRequest(response.urljoin(link),
                                    callback=self.parse_data,
                                    headers=self.headers,
                                    meta={'original_url': link})

    def parse_data(self, response):

        page_url = response.meta['original_url']

        # Cleaning up page URL since Splash adds the port at the end of the URL
        if page_url.startswith('/'):
            page_url = base_url+page_url

        links = response.css('a::attr(href)').getall()

        link_text = response.xpath('//div[@id="app"]//text()').extract()
        link_string = str(link_text)

        for link in links:

            page_url = page_url.replace(":443", "").replace(":80", "")
            # If link has mailto or tel, don't process since this will fail.
            # Call page_dump_null
            if "mailto:" in link or "tel:" in link:
                link_type = "Mailto/Tel"
                yield from self.page_dump_null(page_url,
                                               link,
                                               link_type,
                                               "N/A")
            else:
                # Using regular scrapy to get the response codes for the urls
                yield scrapy.Request(response.urljoin(link),
                                     callback=self.sub_url,
                                     dont_filter=True,
                                     headers=self.headers,
                                     meta={'original_url': page_url})

            # Lorem Ipsum Checker
            for lorem in lorem_set:
                if lorem in link_string:
                    print(f'Found {lorem} in {page_url}')
                    lorem_url_set.add(page_url)
                    break

    # This is called for broken links, tel/mailto links, etc...
    def page_dump_null(self, page_url, link, link_type, link_response):

        # SplashRequest appends the port number at the end on original request.
        # Removing these if detected.
        page_url = page_url.replace(":443", "").replace(":80", "").strip("/")

        yield {
            "Page": page_url,
            "Link": link,
            "Link Type": link_type,
            "Link Response": link_response
        }

    # Checks urls on page
    # calls page_dump_null() for pages that report bad response codes.
    def sub_url(self, response):

        page_url = response.meta['original_url']

        response_code = response.status
        link = response.url

        if 200 <= response_code and response_code <= 299:

            if check_url in link or link.startswith("/"):
                link_type = "Local"

                # Adding local URL to URL set, dumps to txt file at end.
                # Used to run local links through addl scripts
                url_set.add(str(link))

                if link.startswith("/"):
                    link = base_url+link

            else:
                link_type = "External"

            # Cleaning up page URL as Splash adds the port at the end
            if page_url.startswith('/'):
                page_url = base_url+page_url

            page_url = page_url.replace(":443", "").replace(":80", "")

            # Dumping output
            yield {
                "Page": page_url,
                "Link": link,
                "Link Type": link_type,
                "Link Response": response.status,
            }
        else:
            yield from self.page_dump_null(page_url,
                                           response.url,
                                           'Link',
                                           response.status)

    # When the spider is completed, all local urls are dumped to a txt file.
    def spider_closed(self, spider):

        # File name
        name = check_url.replace("http://", '')\
                        .replace("https://", '')\
                        .split("/")[0]\
                        .split(".")

        # Writing local URLs to txt file as name of site
        f = open(name[0] + "-links.txt", 'w+')
        f.write('\n'.join(map(str, url_set)))
        f.close()

        # Conditional for URLs that contain lorem ipsum.
        if lorem_url_set:
            lf = open(name[0] + "-lorem-check.txt", 'w+')
            lf.write('\n'.join(map(str, lorem_url_set)))
