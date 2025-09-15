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

# ArcGIS Server user
"${psql[@]}" --dbname="gdsc" -c "CREATE ROLE sde WITH LOGIN SUPERUSER NOINHERIT CREATEDB CREATEROLE NOREPLICATION PASSWORD '$SDE_PASSWORD';"

# Authenticator login for APIs
"${psql[@]}" --dbname="gdsc" -c "CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD '$DB_AUTHENTICATOR_PASSWORD';"

# Anonymous (grant select) and token based (grant all) roles
# see: https://postgrest.org/en/stable/tutorials/tut1.html
"${psql[@]}" --dbname="gdsc" <<-'EOSQL'
  -- non-authenticated read role
  CREATE ROLE web_anon NOLOGIN;
  GRANT USAGE ON SCHEMA public TO web_anon;
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO web_anon;
  GRANT web_anon TO authenticator;
  -- authenticated crud role
  CREATE ROLE crud_user NOLOGIN;
  GRANT USAGE ON SCHEMA public TO crud_user;
  GRANT ALL ON ALL TABLES IN SCHEMA public TO crud_user;
  GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO crud_user;
  GRANT crud_user TO authenticator;
EOSQL

# foreign data wrapper, sde user, and remote schema for GDSC proxy
# TODO: change postgres user to the gdsc_manager role
"${psql[@]}" --dbname="gdsc" <<-'EOSQL'
  CREATE EXTENSION IF NOT EXISTS postgres_fdw;
  CREATE EXTENSION IF NOT EXISTS postgis_raster;
  CREATE SCHEMA remote AUTHORIZATION postgres;
EOSQL

# create GDSC functions for GDSC proxy
for script in $(ls /usr/lib/postgresql/16/scripts/*.sql)
do
  sed 's/__USER__/'$POSTGRES_USER'/g' $script | \
  sed 's/__PASS__/'$PGPASSWORD'/g' | \
  "${psql[@]}" --dbname="gdsc"
done