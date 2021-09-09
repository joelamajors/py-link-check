# Py-link-check

This crawler uses Python Scrapy and Splash to crawl websites with dynamic content and test every link on each page and dumps a report of the following:
- Text and json of all local urls under `reports` folder.
- Text file of all local urls which have lorem ipsum (`site-lorem-check.txt`)

If the `-O` is used, this will trigger an output file of the crawler results. The following columns will be generated:
```
            "Page": Page,
            "Page Response": Page response code,
            "Link": Link found on the page,
            "Link Type": Link type (Internal, External or Mailto/Tel)
            "Link Response": Link Response Code ("N/A" if the link type is "Mailto/Tel")
```

## Crawlers
There are several crawlers to choose from:
```
standard: Runs crawler on site to check links on page. This will likely be the one you need.
blog-twill: Runs crawler on the blogs for Twill sites.
aws-standard: Runs the crawler from AWS. This runs the standard crawler from AWS and dumps reports to the daily-link-check S3 bucket.
aws-twill-blog: HM Twill crawler which runs the crawler from AWS. Runs the crawler and dumps the results to the daily-link-check S3 bucket.
```
<br>

## Install requirements
- Verify you have Python3 installed.
    - run `python --version` or `python3 --version`, which should be ≥`3.9.X`.
        > (For all below commands, use whichever works on your machine: `python` or `python3`)
    - if not installed, then go to the [python download site](https://www.python.org/downloads/) and follow download instructions.
- Install boto3 outside of the virtual environment
  - `pip install boto3`
- CD into the repo and create your virtual environment
  - `python3 -m venv venv`
- activate your virtual environment
  - Mac/lunix: `source venv/bin/activate`
  - Windows: `venv/Scripts/Activate`
- Install requirements
    - `pip install -r requirements.txt`

Note: You'll use this virtual environment everytime you use this. This is so pacakages that are needed do not interfer with any global dependencies you have installed.


Next, you'll need to pull the docker image for scrapy-splash. This is used to act like our browser so we can render the JS that's on the page.
```
docker pull scrapinghub/splash
```

---

# How To use

## Start Splash Docker Image
Run the docker image with the following command:
```
docker run --name splash -d -p 8050:8050 --rm scrapinghub/splash
```
<br>

## Running a crawler
- CD into the repo.
- activate your virtual environment
  - Mac/lunix: `source venv/bin/activate`
  - Windows: `venv/Scripts/Activate`
- Change to the `hmscraper/hmscraper` directory
- Depending on the crawler you need, run the following commands:
    - standard
    ``` scrapy crawl standard -a url=https://website.tld -O nameOfWebsite.csv ```
    - blog-twill
    ``` scrapy crawl blog-twill -a url=https://website.tld -O nameOfWebsite.csv ```
    - aws-standard
    ``` scrapy crawl aws-standard -a url=https://website.tld -O nameOfWebsite.csv ```
    - blog-twill
    ``` scrapy crawl blog-twill -a url=https://website.tld -O nameOfWebsite.csv ```

Notes
- The `-O` flag is outputting the status codes to a CSV. You should name this the same name of the name of website without the http|https or the TLD.
- If you do NOT need the CSV report, you can run this without the -O parameter. You will still receieve the urls.txt/json files, and the lorem-ipsum text file if lorem ipsum is detected.
