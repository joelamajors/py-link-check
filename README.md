# py-link-check
Python web scraper using Scrapy/Splash. This is a fast python crawler that checks all links on a page and logs this to a JSON or CSV file.


## Setup
- CD into the `py-link-check` and run `pip3 install requirements.txt`
- CD into the `py-link-check/hmscraper/hmscraper/spiders/hm_standard.py` directory
- Change the `check_url` variable to the URL you're testing with

## To run
- Run crawler normally
```
scrapy crawl standard
```

- Run crawler and dump to CSV or JSON
```
scrapy crawl standard -O filename.json
or 
scrapy crawl standard -O filename.csv
```