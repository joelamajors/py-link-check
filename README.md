Uses Python Scrapy and splash. 

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