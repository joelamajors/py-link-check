#!/bin/bash

# General Summary:
#For each url in the urls.json, run the checker and download the results

# Changing to the directory for the script, activate the virtual environment, and cd to hmscraper/hmscraper
cd /home/ssm-user/scripts/py-link-check

. ./venv/bin/activate

cd hmscraper/hmscraper/

# Copy down the urls.json file here
aws s3 cp s3://daily-link-check/urls.json /home/ssm-user/scripts/py-link-check/hmscraper/hmscraper/urls.json

# Starts Docker
sudo systemctl start docker

# Starts Container
sudo docker run --name splash -d -p 8050:8050 --rm scrapinghub/splash

# variable used to get the current date for for the CSV file
NOW=$(date +"%m-%d-%y")

# Variable used to get the month, this is used to create the month folder in S3
MONTH=$(date +"%b")

# Running command to check to see if the month folder has been created
aws s3 ls s3://daily-link-check/"$MONTH"

# If the month folder is not created, create this and the sub folders
if  [[ $? -ne 0 ]]; then

    aws s3api put-object --bucket daily-link-check --key "$MONTH"/reports/
    aws s3api put-object --bucket daily-link-check --key "$MONTH"/links/
    aws s3api put-object --bucket daily-link-check --key "$MONTH"/lorem/
fi

# Now we loop through the urls.json file and run the link-check script. 
jq -c -r '.urls[]' urls.json | while read i; do
    name=$(echo $i |  awk -F[/:] '{print $4}' | cut -f1 -d".")
    scrapy crawl aws-standard -a url="$i" -O ./reports/"$NOW"_"$name".csv

    # Variables used for  checking API endpoint for twill sites. If the site is Twill site, then the blogs get checked via a separate script. Removes trailing slash
    VAR=$(echo $i | sed -e 's#/$##')

    # Variable for the API enpoints. This checks via a curl request. 
    API_ENDPOINTS=$(curl -L $VAR/api/posts)

    # Checking to see if the site is a twill site. If so, we want to run the blog check on this blogs as well. 
    if [[ $API_ENDPOINTS ]]; then
        scrapy crawl aws-twill-blog -a url="$VAR/api/posts" -O ./reports/"$NOW"_blog_"$name".csv
    fi

done