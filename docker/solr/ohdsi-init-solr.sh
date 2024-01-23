#!/bin/bash

./bin/solr create -c gaia
echo '<delete><query>*:*</query></delete>' | ./bin/post -c gaia -d
./bin/post -c gaia -filetypes json $(find /collections -name 'dcat_*.json' -type f)