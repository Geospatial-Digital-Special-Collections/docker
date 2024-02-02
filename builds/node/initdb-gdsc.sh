
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