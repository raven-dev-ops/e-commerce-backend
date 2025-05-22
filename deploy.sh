#!/bin/bash

APP_NAME="twiinz-beard-website"
HEROKU_IMAGE_TAG="registry.heroku.com/$APP_NAME/web" # Define it once

echo "Logging into Heroku container registry..."
heroku container:login

echo "Setting Heroku stack to container..."
heroku stack:set container -a $APP_NAME

echo "Building new Docker image (linux/amd64) directly with Heroku tag..."
# Build directly with the Heroku tag. The :latest is implicit if not specified.
docker build --platform=linux/amd64 --no-cache -t $HEROKU_IMAGE_TAG .

# The 'docker tag' command is no longer needed as we built with the correct tag.
# echo "Tagging Docker image..."
# docker tag main:latest $HEROKU_IMAGE_TAG # REMOVE THIS LINE

echo "Pushing Docker image..."
docker push $HEROKU_IMAGE_TAG # This will push registry.heroku.com/twiinz-beard-website/web:latest

echo "Releasing Docker container..."
# Heroku container:release web will look for the 'web' image type, which by default is tagged 'latest'
# which we just pushed.
heroku container:release web -a $APP_NAME

echo "Checking if web dyno is running..."
# Give a few seconds for the release to potentially start a dyno
sleep 5 
DYNO_COUNT=$(heroku ps -a $APP_NAME --json | jq '.[] | select(.type=="web")' | jq -s 'length')

if [ "$DYNO_COUNT" -eq "0" ]; then
  echo "No web dyno running. Scaling web dyno to 1..."
  heroku ps:scale web=1 -a $APP_NAME
else
  echo "Web dyno already running or starting."
fi

echo "Checking process status..."
heroku ps -a $APP_NAME

echo "Tailing logs..."
heroku logs --tail -a $APP_NAME