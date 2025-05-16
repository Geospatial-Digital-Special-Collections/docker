#!/bin/bash

# build the intial indexes for collections and data respectively
./bin/solr post --solr-url http://localhost:8983 -c collections -filetypes json $(find /data/collections -not \( -path /data/collections/lost+found -prune \) -name 'meta_*.json' -type f)
./bin/solr post --solr-url http://localhost:8983 -c dcat -filetypes json $(find /data/data -not \( -path /data/data/lost+found -prune \) -name 'meta_dcat*.json' -type f)