#
# NOTE: THIS DOCKERFILE IS GENERATED VIA "make update"! PLEASE DO NOT EDIT IT DIRECTLY.
#

FROM postgres:15-bullseye

LABEL maintainer="PostGIS Project - https://postgis.net" \
      org.opencontainers.image.description="PostGIS 3.5.2+dfsg-1.pgdg110+1 spatial database extension with PostgreSQL 15 bullseye" \
      org.opencontainers.image.source="https://github.com/postgis/docker-postgis"

ENV POSTGIS_MAJOR 3
ENV POSTGIS_VERSION 3.5.2+dfsg-1.pgdg110+1

RUN apt-get update \
      && apt-cache showpkg postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
      && apt-get install -y --no-install-recommends \
           # ca-certificates: for accessing remote raster files;
           #   fix: https://github.com/postgis/docker-postgis/issues/307
           ca-certificates \
           \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR=$POSTGIS_VERSION \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts \
      && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /docker-entrypoint-initdb.d
COPY ./builds/proxy/initdb-postgis.sh /docker-entrypoint-initdb.d/10_postgis.sh
COPY ./builds/proxy/update-postgis.sh /usr/local/bin

# install gdal raster command line tools
RUN apt-get update -y \
    && apt-get install postgis -y \
    && apt-get clean \
    && rm -rf /var/cache/apt/lists/*

# provide the ArcGIS geometry libraries for postGIS
ENV LD_LIBRARY_PATH /usr/lib/postgresql
COPY ./config/ESRI/PostgreSQL/12/Linux64/st_geometry.so /usr/lib/postgresql/15/lib
RUN chmod 644 /usr/lib/postgresql/15/lib/st_geometry.so

# provide function to create foreign data wrappers, foreign tables, and views
RUN mkdir /usr/lib/postgresql/15/scripts
COPY ./scripts/sql /usr/lib/postgresql/15/scripts