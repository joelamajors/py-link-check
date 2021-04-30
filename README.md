This crawler uses Python Scrapy and Splash to crawl websites with dynamic content and test every link on each page and dumps a report of the following:
- text file of all local urls
- if the `-O` flag is used - a report of the page, links found, local/external, mailto/tel and reponse code will be output to a CSV or JSON file.

## Setup Scrapy

Pull the image if you haven't

```
sudo docker pull scrapinghub/splash
```

run it

```
docker run -it -p 8050:8050 --rm scrapinghub/splash
```

## Install requirements

- CD into the repo and run `pip3 install -r requirements.txt`

## To run:

CD into the `py-link-check/hmscraper/hmscraper/spiders/hm_standard.py` directory

Change the `check_url` variable to the URL you're testing with

Run with no output file

```
scrapy crawl standard
```

Run with output file

```
scrapy crawl standard -O beepboop.csv

or 

scrapy crawl standard -O beepboop.json
```

## Reports
The list of URLs are saved under repo/hmscraper/SITE-links.txt. The report generated with the `-O` flag will be saved in the same directory with the name you've provided.