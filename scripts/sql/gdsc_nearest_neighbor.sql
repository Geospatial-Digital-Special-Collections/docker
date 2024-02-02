-- FUNCTION: public.gdsc_nearest_neighbor(regclass, numeric, numeric, text)

-- DROP FUNCTION public.gdsc_nearest_neighbor(regclass, numeric, numeric, text);

CREATE OR REPLACE FUNCTION public.gdsc_nearest_neighbor(
  tablename regclass,
  lat numeric,
  lng numeric,
  identifier text)
    RETURNS json
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$

DECLARE
neighbor_result record;
srs_result record;

BEGIN

-- get the layer srs
EXECUTE 'SELECT Find_SRID(''public'',''' || tablename || ''', ''geom_local'') AS srs;' INTO srs_result;

-- execute the query
EXECUTE '
  SELECT 
    ' || tablename || '.' || identifier || ',
    ' || tablename || '.geom_local <-> ST_Transform(ST_GeomFromText(''POINT(' || lng || ' ' || lat || ')'',4326), ' || srs_result.srs || ')::geometry AS dist
  FROM
   ' || tablename || '
  ORDER BY
    dist
  LIMIT 1;
' INTO neighbor_result;

RETURN json_agg(neighbor_result);

END;
$BODY$;

ALTER FUNCTION public.gdsc_nearest_neighbor(regclass, numeric, numeric, text)
    OWNER TO postgres;

NOTIFY pgrst, 'reload schema'