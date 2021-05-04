This crawler uses Python Scrapy and Splash to crawl websites with dynamic content and test every link on each page and dumps a report of the following:
- text file of all local urls
- if the `-O` flag is used - a report of the page, links found, local/external, mailto/tel and reponse code will be output to a CSV or JSON file.

## Setup Scrapy

If this is the first time you're running this tool, you'll need to pull the image. Run the following command in a terminal window.

```
docker pull scrapinghub/splash
```

Now we need to run the docker image:

```
docker run -it -p 8050:8050 --rm scrapinghub/splash
```

## Install requirements
- Verify you have Python3 installed. If not, install this.
- Clone the repo and CD into the repo.
- Install the following modules by running these commands in our terminal 
``` pip3 install scrapy ```
``` pip3 install scrapy-splash ```

## To run:
- Change into the `py-link-check/hmscraper` directory
- Open the ```hm_standard.py``` (py-link-check\hmscraper\hmscraper\spiders\hm_standard.py). Change the URL to match the one you need to test. 

Now we can run the spider. We can run this one of two ways:

### Run with no output file

```
scrapy crawl standard
```

### Run with output file

```
scrapy crawl standard -O beepboop.csv

or 

scrapy crawl standard -O beepboop.json
```

Make sure you're in the hmscraper directory. Otherwise you'll get an error. 

## Reports
The list of URLs are saved under repo/hmscraper/SITE-links.txt. The report generated with the `-O` flag will be saved in the same directory with the name you've provided.
