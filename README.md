# Py-link-check

This crawler uses Python Scrapy and Splash to crawl websites with dynamic content and test every link on each page and dumps a report of the following:
- text file of all local urls (which can be used for other tools like page-reporter, lorem-ipsum checker, etc.)
- text file of all of urls that have lorem ipsum (`site-lorem-check.txt`)

If the `-O` is used, this will trigger an output file of the crawler results. The following columns will be generated:
```
            "Page": Page,
            "Page Response": Page response code,
            "Link": Link found on the page,
            "Link Type": Link type (Internal, External or Mailto/Tel)
            "Link Response": Link Response Code ("N/A" if the link type is "Mailto/Tel")
```

There's currently two crawlers in this package. Once is for standard URLs (hm_standard) and another is for blog URLs in twill (hm_blog). The crawlers are located under `hmcraper/hmscraper/spiders` and are called:
```
hm_blog
hm_standard
```
<br>

## Setup Scrapy
This tool uses Splash to act as a proxy to render dynamic pages in a browser. Fortunately Splash can be setup with docker using only 2 lines.

If this is the first time you're running this tool, you'll need to pull the image. If you've already ran this tool before - you do not need to pull it and can move to the next step.   Pull the docker image by running this in terminal:
```
docker pull scrapinghub/splash
```
Next we need to run the docker image with the following command:
```
docker run -it -p 8050:8050 --rm scrapinghub/splash
```
<br>

## Install requirements
- Verify you have Python3 installed. If not, install this.
- Clone the repo and CD into the repo.
- Install the following modules by running these commands in our terminal:
``` 
pip3 install scrapy
pip3 install scrapy-splash
```
<br>

## To run:

#### Setup URL in script
- Open the file of the spider your about to use (hm_blog or hm_standard).
- Change the URL variable to be the base url for the site.
	- For example:
    ``` http://aac.hatfield.marketing/ ```
<br>

#### Runing script
We can run this tool several different ways. This is generally ran with the `-O` flag which generates a CSV or JSON file of all the columns provided above. In addition, you can run this without any flags and generate the local URLs list if that is all you need. You can call the crawler with the following names:
#### Crawler names
- standard - standard URL crawler
- hmblog_twill - crawler for hmtwill blogs 
<br>

##### Run with no output file

```
scrapy crawl standard
```
<br>

##### Run with output file
Run the command with the `-O` flag indicating we want to generate an output file and supply the name of the outfile. 
<br>
CSV output:
```
scrapy crawl standard -O beepboop.csv
```
  
JSON output:  
```
scrapy crawl standard -O beepboop.json
```
<br>

##### Run with no output to terminal
Run the spider with the `-L WARN` flag and parameter. Additional parameters can be found in Scrapy documentation.
<br>

```
scrapy crawl SPIDER_NAME -L WARN

scrapy crawl SPIDER_NAME -O beepboop.csv -L WARN

etc...
```

<br>

### List of URLs
Regardless if you run the crawler with or without the -O output, they will generate a list of all local URLs & the lorem ipsum text files (if detected) and save then under repo/hmscraper/... 
