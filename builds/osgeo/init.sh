#!/bin/bash

export PGPASSWORD=$POSTGRES_PASSWORD

echo "machine urs.earthdata.nasa.gov login $USGS_USER password $USGS_PASSWORD" > ~/.netrc
chmod 0600 ~/.netrc
touch ~/.urs_cookies

tail -F /dev/null