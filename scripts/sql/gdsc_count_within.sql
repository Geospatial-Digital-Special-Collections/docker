-- FUNCTION: public.gdsc_count_within(regclass, numeric, numeric, integer)

-- DROP FUNCTION public.gdsc_count_within(regclass, numeric, numeric, integer);

CREATE OR REPLACE FUNCTION public.gdsc_count_within(
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
count_result record;
srs_result record;

BEGIN

-- get the local srs
EXECUTE 'SELECT Find_SRID(''public'',''' || tablename || ''', ''geom_local'') AS srs;' INTO srs_result;

-- execute the query
EXECUTE '
  WITH
     -- our buffer
     buffer AS (SELECT ST_Buffer( ST_Transform(ST_GeomFromText(''POINT(' || lng || ' ' || lat || ')'',4326), ' || srs_result.srs || '), ' || radius || ', ''quad_segs=8'') as geom)
  SELECT count(*) FROM ' || tablename || ', buffer WHERE ST_WITHIN(' || tablename || '.geom_local,buffer.geom);
' INTO count_result;

RETURN json_agg(count_result);

END;
$BODY$;

ALTER FUNCTION public.gdsc_count_within(regclass, numeric, numeric, integer)
    OWNER TO postgres;

NOTIFY pgrst, 'reload schema';
