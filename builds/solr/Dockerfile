# start from an official solr base image
FROM solr

# copy the solr indices
COPY ./metadata/solr/ /var/solr/data

# copy the collection metadata
USER root
RUN mkdir -p /gaia/data && \
    mkdir -p /gaia/collections
COPY ./metadata/data/* /gaia/data
COPY ./metadata/collections/* /gaia/collections
RUN chown -R solr:solr /gaia
USER solr
