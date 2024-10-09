# start from an official solr base image
FROM solr

USER root

# copy the solr indices
COPY ./metadata/solr/ /var/solr/data
RUN chown -R solr:solr /var/solr/data

# copy the collection metadata
RUN mkdir -p /gaia/data && \
    mkdir -p /gaia/collections
COPY ./metadata/data/* /gaia/data
COPY ./metadata/collections/* /gaia/collections
RUN chown -R solr:solr /gaia

USER solr
