#!/bin/bash

set -e

# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

# Create the 'template_postgis' template db
"${psql[@]}" <<- 'EOSQL'
CREATE DATABASE template_postgis IS_TEMPLATE true;
EOSQL

# Load PostGIS into both template_database and $POSTGRES_DB
for DB in template_postgis "$POSTGRES_DB"; do
	echo "Loading PostGIS extensions into $DB"
	"${psql[@]}" --dbname="$DB" <<-'EOSQL'
		CREATE EXTENSION IF NOT EXISTS postgis;
		CREATE EXTENSION IF NOT EXISTS postgis_topology;
		-- Reconnect to update pg_setting.resetval
		-- See https://github.com/postgis/docker-postgis/issues/288
		\c
		CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
		CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
EOSQL
done

# for all GDSC containers
"${psql[@]}" --dbname="gdsc" <<-'EOSQL'
  -- not needed in GDSC
  DROP EXTENSION IF EXISTS postgis_topology;
  DROP EXTENSION IF EXISTS postgis_tiger_geocoder;
  DROP EXTENSION IF EXISTS fuzzystrmatch;
EOSQL

# raster extensions
"${psql[@]}" --dbname="gdsc" <<-'EOSQL'
  CREATE EXTENSION IF NOT EXISTS postgis_raster;
EOSQL