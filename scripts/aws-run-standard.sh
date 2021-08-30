#!/bin/bash

#For each url in the urls.json, run the checker and download the results

cd /home/ssm-user/scripts/py-link-check

. ./venv/bin/activate

cd hmscraper/hmscraper/

aws s3 cp s3://daily-link-check/urls.json /home/ssm-user/scripts/py-link-check/hmscraper/hmscraper/urls.json

# Checks to see if docker service is running
if systemctl is-active --quiet docker; then
    sudo systemctl start docker
else
    echo "Docker is already running"
fi

# Checking to see if container is running
if [ ! "$(sudo docker ps -q -f name=splash)" ]; then
	sudo docker run --name splash -d -p 8050:8050 --rm scrapinghub/splash
else
        echo "Docker image is running!"
fi

NOW=$(date +"%m-%d-%y")

MONTH=$("$b")

# If the month folder is not created, create this and the sub folders
if  [ ! $(aws s3 ls s3://daily-link-check/"$MONTH" | head) ]
then
    aws s3api put-object --bucket daily-link-check --key "$MONTH"/reports/
    aws s3api put-object --bucket daily-link-check --key "$MONTH"/links/
    aws s3api put-object --bucket daily-link-check --key "$MONTH"/lorem/
fi

# Now loop through the urls and run the script
jq -c -r '.urls[]' urls.json | while read i; do
    name=$(echo $i |  awk -F[/:] '{print $4}' | cut -f1 -d".")
    scrapy crawl aws-standard -a url="$i" -O ./reports/"$NOW"_"$name".csv
done
