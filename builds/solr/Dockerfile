# start from an official solr base image
FROM solr

USER root

# copy the empty solr indices
COPY ./metadata/solr/ /var/solr/data
RUN chown -R solr:solr /var/solr/data

# copy the init script
COPY ./init.sh  /docker-entrypoint-initdb.d && chmod +x /docker-entrypoint-initdb.d/init.sh

USER solr
