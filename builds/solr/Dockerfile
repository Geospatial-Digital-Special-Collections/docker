# start from an official solr base image
FROM solr

# copy the solr indices
COPY ./metadata/solr/* /var/solr/data

# copy the collection metadata
RUN mkdir /var/ohdsi/metadata && \
    mkdir /var/ohdsi/metadata/data && \
    mkdir /var/ohdsi/metadata/collections
COPY ./metadata/data/* /var/ohdsi/metadata/data
COPY ./metadata/collections/* /var/ohdsi/metadata/collections
