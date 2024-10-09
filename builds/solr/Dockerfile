# start from an official solr base image
FROM solr

# copy the solr indices
COPY ./metadata/solr/* /var/solr/data

# copy the collection metadata
RUN mkdir -p /var/ohdsi/data && \
    mkdir -p /var/ohdsi/collections
COPY ./metadata/data/* /var/ohdsi/data
COPY ./metadata/collections/* /var/ohdsi/collections
