-- FUNCTION: public.gdsc_zonal_statistics(regclass, numeric, numeric, integer)

-- DROP FUNCTION public.gdsc_zonal_statistics(regclass, numeric, numeric, integer);

CREATE OR REPLACE FUNCTION public.gdsc_zonal_statistics(
  tablename regclass,
  lat numeric,
  lng numeric,
  radius integer)
    RETURNS json
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$

DECLARE
zonal_result record;
srs_result record;

BEGIN

-- get the local srs
EXECUTE 'SELECT ST_SRID(rast) AS srs FROM ' || tablename || ' WHERE rid = 1;' INTO srs_result;

-- execute the query
EXECUTE '
    WITH
  -- our buffer
     buffer AS (SELECT ST_Buffer( ST_Transform(ST_GeomFromText(''POINT(' || lng || ' ' || lat || ')'',4326), ' || srs_result.srs || '), ' || radius || ', ''quad_segs=8'') as geom),
  -- clip the raster to boundaries of buffer
     b_stats AS (
     SELECT (stats).* 
     FROM (
      SELECT ST_SummaryStats(ST_Clip(rast,1,geom,true)) AS stats
      FROM ' || tablename || '
      INNER JOIN buffer ON ST_INTERSECTS(buffer.geom,rast)
     ) AS foo
     )
  SELECT * FROM b_stats
' INTO zonal_result;

RETURN json_agg(zonal_result);

END;
$BODY$;

ALTER FUNCTION public.gdsc_zonal_statistics(regclass, numeric, numeric, integer)
    OWNER TO postgres;

NOTIFY pgrst, 'reload schema';
