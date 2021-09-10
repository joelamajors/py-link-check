#!/bin/bash

#For each url in the urls.json, run the checker and download the results

cd /home/ssm-user/scripts/py-link-check

. ./venv/bin/activate

cd hmscraper/hmscraper/

aws s3 cp s3://daily-link-check/urls.json /home/ssm-user/scripts/py-link-check/hmscraper/hmscraper/urls.json

# Starts Docker
sudo systemctl start docker

# Starts Container
sudo docker run --name splash -d -p 8050:8050 --rm scrapinghub/splash

NOW=$(date +"%m-%d-%y")

MONTH=$(date +"%b")

# Running command to check to see if the month folder has been created
aws s3 ls s3://daily-link-check/"$MONTH"

# If the month folder is not created, create this and the sub folders
if  [[ $? -ne 0 ]]; then

    aws s3api put-object --bucket daily-link-check --key "$MONTH"/reports/
    aws s3api put-object --bucket daily-link-check --key "$MONTH"/links/
    aws s3api put-object --bucket daily-link-check --key "$MONTH"/lorem/
fi

# Now loop through the urls and run the script
jq -c -r '.urls[]' urls.json | while read i; do
    name=$(echo $i |  awk -F[/:] '{print $4}' | cut -f1 -d".")
    scrapy crawl aws-standard -a url="$i" -O ./reports/"$NOW"_"$name".csv

    # Setting variable for API endpoint to test for Twill sites. Removes trailing slash if it's present
    VAR=$(echo $i | sed -e 's#/$##')

    # Variable for the API enpoints
    API_ENDPOINTS=$(curl -L $VAR/api/posts)

    # Checking to see if the site is a twill site. If so, we want to run the blog check on this blogs as well. 
    if [[ $API_ENDPOINTS ]]; then
        scrapy crawl aws-twill-blog -a url="$VAR/api/posts" -O ./reports/"$NOW"_blog_"$name".csv
    fi

done