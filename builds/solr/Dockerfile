# start from an official solr base image
FROM solr

# copy the solr indices
COPY ./metadata/solr/* /var/solr/data

# copy the collection metadata
USER root
RUN mkdir -p /ohdsi/data && \
    mkdir -p /ohdsi/collections
COPY ./metadata/data/* /ohdsi/data
COPY ./metadata/collections/* /ohdsi/collections
RUN chown -R solr:solr /metadata
USER solr
